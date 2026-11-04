"""Tiện ích dùng chung cho spike round-trip.

Không cần thư viện ngoài (chỉ stdlib).

QUY TẮC AN TOÀN cho lệnh ghi (create/update) — xem CLAUDE.md, không nới:
  - localhost: luôn được ghi.
  - Host khác: chỉ khi môi trường khai báo  role = "dev"  VÀ  allow_write = true,
    và người chạy xác nhận tên host (hoặc truyền --yes).
  - role "stg" / "prod" (hoặc thiếu role): KHÔNG BAO GIỜ ghi, dù allow_write là gì.
"""
from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SPIKE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SPIKE_DIR / "data"

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
WRITABLE_ROLES = {"dev"}


class UnsafeTargetError(RuntimeError):
    pass


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def env_settings(cfg: dict, env: str) -> dict:
    try:
        e = cfg["environments"][env]
    except KeyError:
        sys.exit(f"Không có môi trường '{env}' trong config")
    key = os.environ.get(e["api_key_env"])
    if not key:
        sys.exit(f"Chưa đặt biến môi trường {e['api_key_env']} (API key)")
    return {**e, "name": env, "api_key": key}


def host_of(base_url: str) -> str:
    return (urlparse(base_url).hostname or "").lower()


def is_local(base_url: str) -> bool:
    h = host_of(base_url)
    return h in LOCAL_HOSTS or h.endswith(".localhost")


def assert_writable(env: dict) -> None:
    """Chặn ghi nếu môi trường không phải localhost hoặc dev đã bật ghi."""
    if is_local(env["base_url"]):
        return
    role = env.get("role")
    if role not in WRITABLE_ROLES or env.get("allow_write") is not True:
        raise UnsafeTargetError(
            f"Từ chối ghi vào '{host_of(env['base_url'])}' (môi trường '{env.get('name')}', "
            f"role={role!r}, allow_write={env.get('allow_write')!r}). "
            "Chỉ localhost hoặc môi trường role='dev' + allow_write=true mới được ghi."
        )


def confirm_write(env: dict, assume_yes: bool) -> None:
    """Gọi 1 lần trước khi ghi vào host không phải localhost."""
    assert_writable(env)
    if is_local(env["base_url"]) or assume_yes:
        return
    host = host_of(env["base_url"])
    print(f"⚠ Sắp GHI cấu hình site vào: {env['base_url']} (môi trường '{env['name']}', role=dev)")
    ans = input(f"Gõ lại tên host '{host}' để xác nhận: ").strip().lower()
    if ans != host:
        raise SystemExit("Đã hủy.")


def _ssl_context(env: dict) -> ssl.SSLContext | None:
    ca = env.get("ca_bundle")
    return ssl.create_default_context(cafile=ca) if ca else None


def post(env: dict, path: str, body: dict, *, write: bool) -> dict:
    if write:
        assert_writable(env)
    url = env["base_url"].rstrip("/") + path
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60, context=_ssl_context(env)) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as ex:
        detail = ex.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"HTTP {ex.code} tại {path}: {detail}") from ex


def api_body(cfg: dict, env: dict, **extra: Any) -> dict:
    return {"ApiVersion": cfg.get("api_version", 1.1), "ApiKey": env["api_key"], **extra}


def extract_site(resp: dict) -> dict:
    """Lấy phần dữ liệu site từ response. Cấu trúc response cần xác nhận ở Bước 0;
    hàm này chấp nhận vài dạng phổ biến, nếu không khớp thì trả nguyên response."""
    r = resp.get("Response", resp)
    if isinstance(r, dict):
        data = r.get("Data", r)
        if isinstance(data, list) and len(data) == 1:
            return data[0]
        if isinstance(data, dict):
            return data
    return resp


def normalize(obj: Any, volatile: set[str], nested: set[str] | None = None, _depth: int = 0) -> Any:
    """Sắp key ổn định, bỏ trường biến động. Giữ nguyên thứ tự mảng
    (thứ tự cột trong GridColumns/EditorColumnHash có ý nghĩa).

    volatile: chỉ bỏ ở CẤP SITE (depth 0) — vd SiteId, UpdatedTime của chính site.
    nested:   bỏ ở mọi cấp. Mặc định rỗng: SiteId lồng bên trong (Link, lookup…)
              là tham chiếu chéo site, PHẢI giữ lại để phát hiện (review A3)."""
    nested = nested or set()
    drop = (volatile | nested) if _depth == 0 else nested
    if isinstance(obj, dict):
        return {k: normalize(obj[k], volatile, nested, _depth + 1) for k in sorted(obj) if k not in drop}
    if isinstance(obj, list):
        return [normalize(v, volatile, nested, _depth + 1) for v in obj]
    return obj


def volatile_sets(cfg: dict) -> tuple[set[str], set[str]]:
    return set(cfg.get("volatile_keys", [])), set(cfg.get("volatile_nested_keys", []))


def diff(a: Any, b: Any, path: str = "$") -> list[dict]:
    """Diff đệ quy. Trả danh sách {path, kind, before, after}."""
    out: list[dict] = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            p = f"{path}.{k}"
            if k not in b:
                out.append({"path": p, "kind": "removed", "before": a[k], "after": None})
            elif k not in a:
                out.append({"path": p, "kind": "added", "before": None, "after": b[k]})
            else:
                out.extend(diff(a[k], b[k], p))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append({"path": path, "kind": "length", "before": len(a), "after": len(b)})
        for i, (x, y) in enumerate(zip(a, b)):
            out.extend(diff(x, y, f"{path}[{i}]"))
    elif a != b:
        out.append({"path": path, "kind": "changed", "before": a, "after": b})
    return out


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
                    encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def top_area(p: str) -> str:
    """Nhóm diff theo khu vực cấp 2 (vd $.SiteSettings.Columns) để báo cáo."""
    parts = p.replace("[", ".[").split(".")
    return ".".join(parts[:3]) if len(parts) >= 3 else p
