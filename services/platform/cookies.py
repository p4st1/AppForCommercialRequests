from __future__ import annotations

from typing import Any

from services.platform.constants import BASE_URL


def normalize_cookies(raw: Any) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    return {
        str(key).strip(): str(value).strip()
        for key, value in raw.items()
        if str(key).strip() and str(value).strip()
    }


def with_session_cookie_aliases(cookies: dict[str, str]) -> dict[str, str]:
    normalized = dict(normalize_cookies(cookies))
    jsession = str(normalized.get("JSESSIONID", "") or "").strip()
    host_jsession = str(normalized.get("__Host-JSESSIONID", "") or "").strip()
    if jsession and not host_jsession:
        normalized["__Host-JSESSIONID"] = jsession
    if host_jsession and not jsession:
        normalized["JSESSIONID"] = host_jsession
    return normalized


def xsrf_token(cookies: dict[str, str]) -> str:
    return str(cookies.get("XSRF-TOKEN", "") or "").strip()


def apply_cookies_to_session(
    session: Any,
    cookies: dict[str, str],
    *,
    domain: str = "etp.metal-it.ru",
) -> dict[str, str]:
    normalized = with_session_cookie_aliases(cookies)
    token = xsrf_token(normalized)
    if token:
        session.headers["X-XSRF-TOKEN"] = token

    for key, value in normalized.items():
        key_text = str(key).strip()
        value_text = str(value).strip()
        if not key_text or not value_text:
            continue
        session.cookies.set(key_text, value_text, domain=domain, path="/")
        session.cookies.set(key_text, value_text)
    return normalized


def build_playwright_cookies(
    cookies: dict[str, str],
    *,
    url: str = BASE_URL,
) -> list[dict[str, str]]:
    return [
        {
            "name": name,
            "value": value,
            "url": url,
        }
        for name, value in normalize_cookies(cookies).items()
    ]
