from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from utilities.paths import user_path

EXPORT_KEYWORDS = ("export", "excel", "xlsx", "report")


@dataclass
class NetworkEvent:
    url: str
    method: str
    status: int
    request_headers: dict[str, str] = field(default_factory=dict)
    response_headers: dict[str, str] = field(default_factory=dict)
    post_data: str | None = None
    body_preview: str | None = None


@dataclass
class NetworkTrace:
    request_urls: list[str] = field(default_factory=list)
    response_urls: list[str] = field(default_factory=list)
    events: list[NetworkEvent] = field(default_factory=list)
    request_events: list[NetworkEvent] = field(default_factory=list)
    payload_url: str | None = None
    payload_json: dict[str, Any] | None = None
    route_payload_url: str | None = None


def _append_log_line(log_path: Path, line: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as file:
        file.write(f"{line}\n")


def _resolve_debug_log_path(log_path: str) -> Path:
    candidate = Path(log_path).expanduser()
    if candidate.is_absolute():
        return candidate
    return user_path("logs", candidate.name)


def _request_method(request: Any) -> str:
    value = getattr(request, "method", "")
    if callable(value):
        try:
            return str(value() or "").upper()
        except Exception:
            return ""
    return str(value or "").upper()


def _request_post_data(request: Any) -> str | None:
    value = getattr(request, "post_data", None)
    if callable(value):
        try:
            resolved = value()
            return str(resolved) if resolved is not None else None
        except Exception:
            return None
    if value is None:
        return None
    return str(value)


def _headers_to_dict(raw_headers: Any) -> dict[str, str]:
    if isinstance(raw_headers, dict):
        return {
            str(key): str(value)
            for key, value in raw_headers.items()
            if str(key).strip()
        }
    return {}


def _json_preview(payload: Any, *, limit: int = 1000) -> str:
    try:
        text = json.dumps(payload, ensure_ascii=False, default=str)
    except Exception:
        text = str(payload)
    return text[:limit]


def attach_network_trace(
    page: Any,
    *,
    log_path: str = "export_debug.log",
) -> tuple[NetworkTrace, Callable[[], None]]:
    trace = NetworkTrace()
    debug_log_path = _resolve_debug_log_path(log_path)
    debug_log_path.parent.mkdir(parents=True, exist_ok=True)
    debug_log_path.write_text("", encoding="utf-8")

    def _log(message: str) -> None:
        print(message)
        _append_log_line(debug_log_path, message)

    def _on_request(request: Any) -> None:
        request_url = str(getattr(request, "url", "") or "")
        trace.request_urls.append(request_url)
        _log(f"[REQUEST] {request_url}")

        method = _request_method(request)
        post_data = _request_post_data(request)
        request_headers = _headers_to_dict(getattr(request, "headers", {}))
        trace.request_events.append(
            NetworkEvent(
                url=request_url,
                method=method,
                status=0,
                request_headers=request_headers,
                post_data=post_data,
            )
        )

    def _on_response(response: Any) -> None:
        response_url = str(getattr(response, "url", "") or "")
        trace.response_urls.append(response_url)
        _log(f"[RESPONSE] {response_url}")

        request = getattr(response, "request", None)
        method = _request_method(request) if request is not None else ""
        post_data = _request_post_data(request) if request is not None else None
        request_headers = _headers_to_dict(getattr(request, "headers", {})) if request is not None else {}
        response_headers = _headers_to_dict(getattr(response, "headers", {}))
        status = int(getattr(response, "status", 0) or 0)

        body_preview: str | None = None
        payload_json: dict[str, Any] | None = None
        lower_url = response_url.lower()
        if "trade" in lower_url or "bid" in lower_url:
            try:
                response_json = response.json()
                body_preview = _json_preview(response_json, limit=2000)
                if isinstance(response_json, dict):
                    payload_json = response_json
                else:
                    payload_json = {"data": response_json}

                if ("bidPlaces" in body_preview or '"number"' in body_preview) and trace.payload_json is None:
                    trace.payload_url = response_url
                    trace.payload_json = payload_json
                    _log(f"[FOUND PAYLOAD] {response_url}")
                    _log(body_preview[:1000])
            except Exception:
                pass

        trace.events.append(
            NetworkEvent(
                url=response_url,
                method=method,
                status=status,
                request_headers=request_headers,
                response_headers=response_headers,
                post_data=post_data,
                body_preview=body_preview,
            )
        )

    page.on("request", _on_request)
    page.on("response", _on_response)

    def _detach() -> None:
        try:
            page.remove_listener("request", _on_request)
        except Exception:
            pass
        try:
            page.remove_listener("response", _on_response)
        except Exception:
            pass

    return trace, _detach


def attach_export_route_probe(
    page: Any,
    trace: NetworkTrace,
    *,
    log_path: str = "export_debug.log",
) -> Callable[[], None]:
    debug_log_path = _resolve_debug_log_path(log_path)

    def _log(message: str) -> None:
        print(message)
        _append_log_line(debug_log_path, message)

    def _route_handler(route: Any, request: Any) -> None:
        request_url = str(getattr(request, "url", "") or "")
        lower_url = request_url.lower()
        if any(keyword in lower_url for keyword in EXPORT_KEYWORDS):
            trace.route_payload_url = request_url
            _log(f"[ROUTE EXPORT CANDIDATE] {request_url}")
        try:
            route.continue_()
        except Exception:
            pass

    page.route("**/*", _route_handler)

    def _detach() -> None:
        try:
            page.unroute("**/*", _route_handler)
        except Exception:
            pass

    return _detach


def select_export_event(trace: NetworkTrace) -> NetworkEvent | None:
    for event in reversed(trace.events):
        lower_url = event.url.lower()
        content_type = str(event.response_headers.get("content-type", "") or "").lower()
        content_disposition = str(event.response_headers.get("content-disposition", "") or "").lower()

        if event.status >= 400:
            continue
        if any(keyword in lower_url for keyword in EXPORT_KEYWORDS):
            return event
        if "attachment" in content_disposition:
            return event
        if "excel" in content_type or "spreadsheet" in content_type or "octet-stream" in content_type:
            return event
    return None


def select_export_request_event(trace: NetworkTrace) -> NetworkEvent | None:
    for event in reversed(trace.request_events):
        if any(keyword in str(event.url or "").lower() for keyword in EXPORT_KEYWORDS):
            return event
    return None


def dump_trace_details(trace: NetworkTrace, *, log_path: str = "export_debug.log") -> None:
    debug_log_path = _resolve_debug_log_path(log_path)
    _append_log_line(debug_log_path, "")
    _append_log_line(debug_log_path, "=== TRACE SUMMARY ===")
    _append_log_line(debug_log_path, f"response_urls={len(trace.response_urls)}")
    _append_log_line(debug_log_path, f"request_urls={len(trace.request_urls)}")
    _append_log_line(debug_log_path, f"route_payload_url={trace.route_payload_url or ''}")
    for url in trace.response_urls:
        _append_log_line(debug_log_path, url)

    _append_log_line(debug_log_path, "")
    _append_log_line(debug_log_path, "=== EVENT DETAILS ===")
    for event in trace.events:
        event_json = json.dumps(asdict(event), ensure_ascii=False, default=str)
        _append_log_line(debug_log_path, event_json)

    _append_log_line(debug_log_path, "")
    _append_log_line(debug_log_path, "=== REQUEST EVENT DETAILS ===")
    for event in trace.request_events:
        event_json = json.dumps(asdict(event), ensure_ascii=False, default=str)
        _append_log_line(debug_log_path, event_json)
