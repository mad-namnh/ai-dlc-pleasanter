"""AI Gateway — Lambda behind an internal ALB, calling Claude on Amazon Bedrock.

Pleasanter (server script) calls the gateway over internal VPC HTTP and sends NO key.
The gateway calls Bedrock with the Lambda's IAM role → no API key anywhere.

API
  POST /v1/generate
  {
    "model":      "fast",              # alias, must exist in MODEL_MAP
    "system":     "…",                 # optional
    "prompt":     "…",                 # required
    "max_tokens": 1500,                # capped by MAX_TOKENS_CAP
    "caller":     {"site_id": 1, "record_id": 2, "feature": "ai1"}   # optional, logging only
  }
  200 → {"text": "…", "model": "fast", "stop_reason": "end_turn", "usage": {"input_tokens": n, "output_tokens": n}}
  4xx/5xx → {"error": {"code": "…", "message": "…"}}

  GET /health → {"ok": true}

Environment variables
  MODEL_MAP        JSON alias → Bedrock model id / inference profile id. E.g. {"fast": "<id>"}
  DEFAULT_MODEL    default alias (default "fast")
  MAX_TOKENS_CAP   upper bound for max_tokens (default 2000)
  MAX_PROMPT_CHARS upper bound for system + prompt length (default 20000)
  BEDROCK_READ_TIMEOUT  seconds (default 8 — Pleasanter server scripts are cut off at ~10 s)

Logging: metadata only (caller, model, tokens, latency, error code). Prompt/response content is NEVER logged.
"""
from __future__ import annotations

import base64
import json
import os
import time
from typing import Any, Callable

_client = None  # Bedrock runtime client, created lazily and reused across invocations


def _bedrock():
    global _client
    if _client is None:
        import boto3
        from botocore.config import Config

        _client = boto3.client(
            "bedrock-runtime",
            config=Config(
                connect_timeout=2,
                read_timeout=float(os.environ.get("BEDROCK_READ_TIMEOUT", "8")),
                retries={"max_attempts": 1, "mode": "standard"},
            ),
        )
    return _client


# ---------- HTTP helpers (ALB → Lambda response format) ----------

_STATUS_TEXT = {200: "OK", 400: "Bad Request", 404: "Not Found", 405: "Method Not Allowed",
                413: "Payload Too Large", 429: "Too Many Requests", 502: "Bad Gateway",
                503: "Service Unavailable", 504: "Gateway Timeout", 500: "Internal Server Error"}


def _resp(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "statusDescription": f"{status} {_STATUS_TEXT.get(status, '')}".strip(),
        "isBase64Encoded": False,
        "headers": {"Content-Type": "application/json; charset=utf-8"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def _err(status: int, code: str, message: str) -> dict:
    return _resp(status, {"error": {"code": code, "message": message}})


class BadRequest(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


# ---------- Request parsing & validation ----------

def _settings() -> dict:
    try:
        model_map = json.loads(os.environ.get("MODEL_MAP", "{}"))
    except json.JSONDecodeError:
        model_map = {}
    return {
        "model_map": model_map,
        "default_model": os.environ.get("DEFAULT_MODEL", "fast"),
        "max_tokens_cap": int(os.environ.get("MAX_TOKENS_CAP", "2000")),
        "max_prompt_chars": int(os.environ.get("MAX_PROMPT_CHARS", "20000")),
    }


def parse_request(event: dict, cfg: dict) -> dict:
    raw = event.get("body") or ""
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    try:
        req = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        raise BadRequest("invalid_json", "Body is not valid JSON")
    if not isinstance(req, dict):
        raise BadRequest("invalid_json", "Body must be a JSON object")

    prompt = req.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise BadRequest("missing_prompt", "'prompt' is required")
    system = req.get("system") or ""
    if not isinstance(system, str):
        raise BadRequest("invalid_system", "'system' must be a string")
    if len(prompt) + len(system) > cfg["max_prompt_chars"]:
        raise BadRequest("prompt_too_large", f"system + prompt exceeds {cfg['max_prompt_chars']} characters", 413)

    alias = req.get("model") or cfg["default_model"]
    model_id = cfg["model_map"].get(alias)
    if not model_id:
        raise BadRequest("unknown_model", f"Model alias '{alias}' is not allowed")

    try:
        max_tokens = int(req.get("max_tokens") or 1000)
    except (TypeError, ValueError):
        raise BadRequest("invalid_max_tokens", "'max_tokens' must be a number")
    max_tokens = max(1, min(max_tokens, cfg["max_tokens_cap"]))

    caller = req.get("caller") if isinstance(req.get("caller"), dict) else {}
    caller = {k: caller.get(k) for k in ("site_id", "record_id", "feature") if k in caller}

    return {"alias": alias, "model_id": model_id, "system": system, "prompt": prompt,
            "max_tokens": max_tokens, "caller": caller}


# ---------- Bedrock call ----------

def _error_code(ex: Exception) -> str:
    resp = getattr(ex, "response", None)
    if isinstance(resp, dict):
        return resp.get("Error", {}).get("Code", type(ex).__name__)
    return type(ex).__name__


_UPSTREAM_STATUS = {
    "ThrottlingException": (429, "upstream_throttled"),
    "ServiceQuotaExceededException": (429, "upstream_throttled"),
    "ModelTimeoutException": (504, "upstream_timeout"),
    "ReadTimeoutError": (504, "upstream_timeout"),
    "ConnectTimeoutError": (504, "upstream_timeout"),
    "ServiceUnavailableException": (503, "upstream_unavailable"),
    "ModelNotReadyException": (503, "upstream_unavailable"),
    "AccessDeniedException": (502, "upstream_access_denied"),
    "ValidationException": (502, "upstream_validation"),
    "ResourceNotFoundException": (502, "upstream_model_not_found"),
}


def call_model(client, r: dict) -> dict:
    kwargs: dict[str, Any] = {
        "modelId": r["model_id"],
        "messages": [{"role": "user", "content": [{"text": r["prompt"]}]}],
        "inferenceConfig": {"maxTokens": r["max_tokens"]},
    }
    if r["system"]:
        kwargs["system"] = [{"text": r["system"]}]
    out = client.converse(**kwargs)
    blocks = out.get("output", {}).get("message", {}).get("content", [])
    text = "".join(b.get("text", "") for b in blocks if isinstance(b, dict))
    usage = out.get("usage", {})
    return {
        "text": text,
        "model": r["alias"],
        "stop_reason": out.get("stopReason"),
        "usage": {"input_tokens": usage.get("inputTokens"), "output_tokens": usage.get("outputTokens")},
    }


def _log(**fields) -> None:
    print(json.dumps({"type": "ai_gateway", **fields}, ensure_ascii=False))


# ---------- Entry point ----------

def handler(event: dict, context: Any = None, client_factory: Callable = _bedrock) -> dict:
    method = (event.get("httpMethod") or "").upper()
    path = event.get("path") or ""

    if path == "/health":
        return _resp(200, {"ok": True})
    if path != "/v1/generate":
        return _err(404, "not_found", "No such route")
    if method != "POST":
        return _err(405, "method_not_allowed", "Only POST is supported")

    t0 = time.monotonic()
    try:
        r = parse_request(event, _settings())
    except BadRequest as ex:
        _log(outcome="rejected", code=ex.code)
        return _err(ex.status, ex.code, ex.message)

    try:
        result = call_model(client_factory(), r)
    except Exception as ex:  # classify upstream errors without leaking internal details
        code = _error_code(ex)
        status, public_code = _UPSTREAM_STATUS.get(code, (502, "upstream_error"))
        _log(outcome="upstream_error", code=code, caller=r["caller"], model=r["alias"],
             ms=int((time.monotonic() - t0) * 1000))
        return _err(status, public_code, f"Model call failed ({code})")

    _log(outcome="ok", caller=r["caller"], model=r["alias"], usage=result["usage"],
         stop_reason=result["stop_reason"], ms=int((time.monotonic() - t0) * 1000))
    return _resp(200, result)
