"""Unit tests for the AI gateway — no boto3 or AWS needed (fake Bedrock client).

  python -m unittest discover -s gateway/tests -v
"""
import base64
import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lambda"))
import handler as h  # noqa: E402


class FakeClient:
    def __init__(self, response=None, raises=None):
        self.response, self.raises, self.calls = response, raises, []

    def converse(self, **kw):
        self.calls.append(kw)
        if self.raises:
            raise self.raises
        return self.response


class FakeClientError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.response = {"Error": {"Code": code}}


OK = {"output": {"message": {"content": [{"text": '{"a":'}, {"text": " 1}"}]}},
      "stopReason": "end_turn", "usage": {"inputTokens": 10, "outputTokens": 5}}


def ev(body, path="/v1/generate", method="POST", b64=False):
    raw = json.dumps(body) if not isinstance(body, str) else body
    if b64:
        raw = base64.b64encode(raw.encode()).decode()
    return {"httpMethod": method, "path": path, "body": raw, "isBase64Encoded": b64}


def call(event, client):
    r = h.handler(event, None, client_factory=lambda: client)
    return r["statusCode"], json.loads(r["body"])


class GatewayTest(unittest.TestCase):
    def setUp(self):
        os.environ["MODEL_MAP"] = json.dumps({"fast": "test-model-id"})
        os.environ["MAX_TOKENS_CAP"] = "2000"
        os.environ["MAX_PROMPT_CHARS"] = "100"

    def test_ok_maps_alias_and_joins_text(self):
        c = FakeClient(OK)
        st, b = call(ev({"model": "fast", "system": "s", "prompt": "p", "max_tokens": 50}), c)
        self.assertEqual(st, 200)
        self.assertEqual(b["text"], '{"a": 1}')
        self.assertEqual(b["usage"], {"input_tokens": 10, "output_tokens": 5})
        kw = c.calls[0]
        self.assertEqual(kw["modelId"], "test-model-id")
        self.assertEqual(kw["system"], [{"text": "s"}])
        self.assertEqual(kw["inferenceConfig"], {"maxTokens": 50})

    def test_base64_body_from_alb(self):
        st, _ = call(ev({"prompt": "p"}, b64=True), FakeClient(OK))
        self.assertEqual(st, 200)

    def test_default_model_and_no_system(self):
        c = FakeClient(OK)
        call(ev({"prompt": "p"}), c)
        self.assertEqual(c.calls[0]["modelId"], "test-model-id")
        self.assertNotIn("system", c.calls[0])

    def test_max_tokens_capped(self):
        c = FakeClient(OK)
        call(ev({"prompt": "p", "max_tokens": 999999}), c)
        self.assertEqual(c.calls[0]["inferenceConfig"]["maxTokens"], 2000)

    def test_unknown_model_rejected_without_calling_bedrock(self):
        c = FakeClient(OK)
        st, b = call(ev({"model": "opus-anything", "prompt": "p"}), c)
        self.assertEqual((st, b["error"]["code"]), (400, "unknown_model"))
        self.assertEqual(c.calls, [])

    def test_missing_prompt(self):
        st, b = call(ev({"prompt": "  "}), FakeClient(OK))
        self.assertEqual((st, b["error"]["code"]), (400, "missing_prompt"))

    def test_prompt_too_large(self):
        st, b = call(ev({"prompt": "x" * 101}), FakeClient(OK))
        self.assertEqual((st, b["error"]["code"]), (413, "prompt_too_large"))

    def test_invalid_json(self):
        st, b = call(ev("{not json"), FakeClient(OK))
        self.assertEqual((st, b["error"]["code"]), (400, "invalid_json"))

    def test_routes(self):
        self.assertEqual(call(ev({}, path="/health", method="GET"), FakeClient())[0], 200)
        self.assertEqual(call(ev({}, path="/x"), FakeClient())[0], 404)
        self.assertEqual(call(ev({"prompt": "p"}, method="GET"), FakeClient())[0], 405)

    def test_upstream_errors_mapped(self):
        for code, (status, pub) in {"ThrottlingException": (429, "upstream_throttled"),
                                    "AccessDeniedException": (502, "upstream_access_denied"),
                                    "SomethingNew": (502, "upstream_error")}.items():
            st, b = call(ev({"prompt": "p"}), FakeClient(raises=FakeClientError(code)))
            self.assertEqual((st, b["error"]["code"]), (status, pub), code)

    def test_timeout_by_class_name(self):
        ReadTimeoutError = type("ReadTimeoutError", (Exception,), {})
        st, b = call(ev({"prompt": "p"}), FakeClient(raises=ReadTimeoutError()))
        self.assertEqual((st, b["error"]["code"]), (504, "upstream_timeout"))

    def test_log_has_no_prompt_content(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            call(ev({"prompt": "BI-MAT-KHACH-HANG", "caller": {"site_id": 1, "secret": "x"}}), FakeClient(OK))
        logs = buf.getvalue()
        self.assertNotIn("BI-MAT-KHACH-HANG", logs)
        self.assertNotIn("secret", logs)
        self.assertIn('"site_id": 1', logs)


if __name__ == "__main__":
    unittest.main()
