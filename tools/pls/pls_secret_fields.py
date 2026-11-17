"""Secret-bearing fields of notifications and reminders (L-SEC-01 by path, I7, ADR-0005).

The pattern checks of L-SEC-01 (pls.SECRET_RES) see a secret only when its text looks like one. Some fields of
Pleasanter_1.5.2.0 hold a credential whatever its text looks like (source-derived, Libraries/Settings):

- `Notification.Token` and `Reminder.Token` — the token of ChatWork, LINE, InCircle (Notification.Send,
  Reminder.Remind): a short token passes the pattern checks;
- the webhook URL of an incoming-webhook service: `Notification.Address` of types Slack 2, Teams 6, RocketChat 7,
  LineWorks 10 and `Reminder.To` of types Slack 2, Teams 6, RocketChat 7, LineWorks 9 — the URL itself is the
  credential;
- `Notification.Headers` (HttpClient 9, a JSON object of header names and values — DataSources/HttpClient.cs) with a
  header whose name is credential-like (Authorization, X-API-Key, Ocp-Apim-Subscription-Key, X-Auth, …);
- an HttpClient `Address` with a credential-like query parameter (`?token=…`, `&client_secret=…`, `&sig=…`) or to a
  known incoming-webhook host or path (Slack, Teams / Office, Discord, Zapier), whose URL path is the credential.

- an HttpClient `Address` with user and password (`https://user:pass@host`).

A number in these fields counts as filled, and a type given as its enum name (`"Slack"`) is read as its number, as
Newtonsoft reads them. Limits: a credential under a harmless-looking name, or in the path of an unknown webhook
service, is not seen here (the pattern checks of L-SEC-01 still apply); a name containing one of the credential words
(`X-Author`) is flagged although it is harmless — the check fails closed.

ADR-0005 forbids secrets in SiteSettings (runtime layer 3), and pls resolves no `${secret:…}` reference, while
`${env:…}` values live in environments.json in git — so no form of these values may be kept in configuration.
Process notifications (`Processes[].Notifications`) have the Notification class too: every list named
`Notifications` or `Reminders` is checked, at any depth. Only names are returned, never a value.
"""
from __future__ import annotations

import json
import re
from typing import Any, Iterator

WEBHOOK_NOTIFICATION_TYPES = {2, 6, 7, 10}      # Notification.Types: Slack, Teams, RocketChat, LineWorks
WEBHOOK_REMINDER_TYPES = {2, 6, 7, 9}           # Reminder.ReminderTypes: Slack, Teams, RocketChat, LineWorks
HTTP_CLIENT = 9                                  # Notification.Types.HttpClient
# a header or query parameter name that contains one of these words names a credential
CREDENTIAL_NAME = re.compile(r"(?i)(auth|key|token|secret|passw|pwd|cookie|signature|(^|[-_.])(sig|code)($|[-_.]))")
QUERY_PARAM = re.compile(r"[?&]([^=&#\s]+)=[^&#\s]")
WEBHOOK_URL = re.compile(r"(?i)(hooks\.slack\.com/|webhook\.office\.com/|discord(app)?\.com/api/webhooks/|"
                         r"hooks\.zapier\.com/|/api/webhooks/)")
USERINFO_URL = re.compile(r"(?i)^[a-z][a-z0-9+.\-]*://[^/@\s]+:[^/@\s]*@")      # https://user:pass@host
HINT = ("Pleasanter must hold no credential (ADR-0005): call an internal gateway that authenticates itself "
        "(patterns/ai-gateway/), or use 拡張サーバスクリプト (extended server scripts) on the server")


NAMES = {"notification-token", "reminder-token", "webhook-url", "credential-header", "credential-in-url"}


def _filled(v: Any) -> bool:
    """A value Pleasanter would read as text (Newtonsoft turns a number into a string)."""
    return (isinstance(v, str) and v.strip() != "") or (isinstance(v, (int, float)) and not isinstance(v, bool))


TYPE_NAMES = {"Notifications": {"Slack": 2, "Teams": 6, "RocketChat": 7, "HttpClient": 9, "LineWorks": 10},
              "Reminders": {"Slack": 2, "Teams": 6, "RocketChat": 7, "LineWorks": 9}}


def _type(item: dict, key: str) -> int | None:
    """The type number; an enum name (Newtonsoft accepts "Slack") is read as its number."""
    v = item.get(key)
    if isinstance(v, str) and v.strip() in TYPE_NAMES["Notifications" if key == "Type" else "Reminders"]:
        return TYPE_NAMES["Notifications" if key == "Type" else "Reminders"][v.strip()]
    try:
        return int(v)
    except (TypeError, ValueError, OverflowError):
        return None


def _header_names(text: str) -> list[str]:
    """Header names of a Headers text: the keys of its JSON object; text that is not one is read as a whole."""
    try:
        doc = json.loads(text)
    except ValueError:
        return [text]
    return [str(k) for k in doc] if isinstance(doc, dict) else [text]


def _notification(item: dict) -> Iterator[str]:
    t = _type(item, "Type")
    if _filled(item.get("Token")):
        yield "notification-token"
    if t in WEBHOOK_NOTIFICATION_TYPES and _filled(item.get("Address")):
        yield "webhook-url"
    if _filled(item.get("Headers")) and any(CREDENTIAL_NAME.search(n) for n in _header_names(str(item["Headers"]))):
        yield "credential-header"
    addr = str(item.get("Address") or "")
    if t == HTTP_CLIENT and _filled(addr) and (WEBHOOK_URL.search(addr) or USERINFO_URL.search(addr)
                                                or any(CREDENTIAL_NAME.search(n) for n in QUERY_PARAM.findall(addr))):
        yield "credential-in-url"


def _reminder(item: dict) -> Iterator[str]:
    if _filled(item.get("Token")):
        yield "reminder-token"
    if _type(item, "ReminderType") in WEBHOOK_REMINDER_TYPES and _filled(item.get("To")):
        yield "webhook-url"


def _walk(obj: Any) -> Iterator[str]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("Notifications", "Reminders") and isinstance(v, list):
                for it in v:
                    if isinstance(it, dict):
                        yield from (_notification(it) if k == "Notifications" else _reminder(it))
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v)


def secret_fields(obj: Any) -> list[str]:
    """Sorted names of the secret-bearing fields filled in obj (a model, SiteSettings, a payload or its JSON text)."""
    if isinstance(obj, str):
        try:
            obj = json.loads(obj)
        except ValueError:
            return []
    return sorted(set(_walk(obj)))
