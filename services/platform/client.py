from __future__ import annotations

import logging
import time
from typing import Any

import requests

from services.platform.config import PlatformLoadConfig
from services.platform.constants import (
    BASE_URL,
    DEFAULT_REQUEST_RETRIES,
    DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_RETRY_BACKOFF_SECONDS,
    DEFAULT_SITEMAP_PAGE,
    DEFAULT_USER_AGENT,
    GRAPHQL_ENDPOINT,
    RETRADING_SITEMAP_PAGE,
    TRADE_DETAILS_ENDPOINT_PATTERN,
)
from services.platform.cookies import (
    apply_cookies_to_session,
    normalize_cookies,
    with_session_cookie_aliases,
)
from services.platform.queries import (
    FULL_GRAPHQL_QUERY,
    build_trade_search_payload,
    build_trade_search_variables,
)
from services.platform.trade_parser import (
    normalize_total,
    normalize_trade_json,
    parse_retrade_bids,
    parse_retrades,
    parse_trade_search_response,
)

logger = logging.getLogger(__name__)


class PlatformTimeoutError(RuntimeError):
    """Raised when the platform API does not respond within configured timeouts."""


def _coerce_request_timeout(raw_timeout: Any) -> float | tuple[float, float]:
    if isinstance(raw_timeout, (list, tuple)) and len(raw_timeout) == 2:
        try:
            connect_timeout = float(raw_timeout[0])
            read_timeout = float(raw_timeout[1])
        except (TypeError, ValueError):
            return DEFAULT_REQUEST_TIMEOUT
        return (max(0.1, connect_timeout), max(0.1, read_timeout))

    try:
        timeout = float(raw_timeout)
    except (TypeError, ValueError):
        return DEFAULT_REQUEST_TIMEOUT
    return max(0.1, timeout)


def _is_retryable_request_error(exc: Exception) -> bool:
    request_exceptions = getattr(requests, "exceptions", None)
    retry_types = []
    for name in ("ReadTimeout", "Timeout", "ConnectionError"):
        exc_type = getattr(request_exceptions, name, None)
        if isinstance(exc_type, type):
            retry_types.append(exc_type)
    if retry_types and isinstance(exc, tuple(retry_types)):
        return True

    error_text = str(exc or "").casefold()
    return (
        "read timed out" in error_text
        or "read timeout" in error_text
        or "connection aborted" in error_text
        or "connection reset" in error_text
    )


def _is_timeout_error(exc: Exception) -> bool:
    request_exceptions = getattr(requests, "exceptions", None)
    timeout_types = []
    for name in ("ReadTimeout", "Timeout"):
        exc_type = getattr(request_exceptions, name, None)
        if isinstance(exc_type, type):
            timeout_types.append(exc_type)
    if timeout_types and isinstance(exc, tuple(timeout_types)):
        return True

    error_text = str(exc or "").casefold()
    return "read timed out" in error_text or "read timeout" in error_text


def _format_timeout_message(timeout: float | tuple[float, float]) -> str:
    if isinstance(timeout, tuple):
        timeout_text = f"{timeout[0]:g}/{timeout[1]:g} сек."
    else:
        timeout_text = f"{timeout:g} сек."
    return (
        "Площадка не ответила на запрос за "
        f"{timeout_text} Попробуйте уменьшить лимит загрузки или повторить позже."
    )


def get_trade_json(platform_client: Any, trade_id: int) -> dict[str, Any]:
    if platform_client is None:
        raise ValueError("platform_client не передан")

    try:
        trade_id_int = int(trade_id)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Некорректный trade_id: {trade_id}") from exc
    if trade_id_int <= 0:
        raise ValueError(f"Некорректный trade_id: {trade_id_int}")

    session = getattr(platform_client, "session", None)
    if session is None:
        raise RuntimeError("У platform_client отсутствует session")

    headers = getattr(platform_client, "headers", None)
    timeout = _coerce_request_timeout(
        getattr(platform_client, "_timeout", DEFAULT_REQUEST_TIMEOUT)
    )
    base_url = str(getattr(platform_client, "BASE_URL", BASE_URL))

    endpoint = TRADE_DETAILS_ENDPOINT_PATTERN.format(
        base_url=base_url.rstrip("/"),
        trade_id=trade_id_int,
    )
    request_with_retries = getattr(platform_client, "_request_with_retries", None)
    if callable(request_with_retries):
        response = request_with_retries("get", endpoint, headers=headers, timeout=timeout)
    else:
        response = session.get(endpoint, headers=headers, timeout=timeout)
    if response.status_code == 403:
        raise RuntimeError("Ошибка авторизации — обновите cookies")
    response.raise_for_status()

    try:
        body = response.json()
    except ValueError:
        logger.warning("Trade details response is not valid JSON for trade_id=%s", trade_id_int)
        return {}
    return normalize_trade_json(body)


def get_retrading_offers(platform_client: Any, trade_id: int) -> list[dict]:
    trade_json = get_trade_json(platform_client, trade_id)
    return parse_retrade_bids(trade_json)


class MetalITClient:
    BASE_URL = BASE_URL
    ENDPOINT = GRAPHQL_ENDPOINT
    DEFAULT_SITEMAP_PAGE = DEFAULT_SITEMAP_PAGE
    RETRADING_SITEMAP_PAGE = RETRADING_SITEMAP_PAGE
    DEFAULT_USER_AGENT = DEFAULT_USER_AGENT

    _normalize_cookies = staticmethod(normalize_cookies)
    _with_session_cookie_aliases = staticmethod(with_session_cookie_aliases)
    _build_variables = staticmethod(build_trade_search_variables)
    _normalize_total = staticmethod(normalize_total)

    def __init__(
        self,
        cookies: dict[str, str],
        *,
        timeout: float | tuple[float, float] | None = None,
        retries: int = DEFAULT_REQUEST_RETRIES,
        retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
        session: requests.Session | None = None,
    ) -> None:
        load_config = PlatformLoadConfig.from_config()
        self.default_limit = load_config.default_limit
        self.default_max_items = load_config.max_items
        configured_timeout = load_config.timeout if timeout is None else timeout
        self._timeout = _coerce_request_timeout(configured_timeout)
        try:
            self._request_retries = max(0, int(retries))
        except (TypeError, ValueError):
            self._request_retries = DEFAULT_REQUEST_RETRIES
        try:
            self._retry_backoff_seconds = max(0.0, float(retry_backoff_seconds))
        except (TypeError, ValueError):
            self._retry_backoff_seconds = DEFAULT_RETRY_BACKOFF_SECONDS
        self._session = session or requests.Session()
        self.session = self._session
        self.headers = self.session.headers
        self.url = self.ENDPOINT
        self.retrades: list[dict[str, Any]] = []
        self.last_trades_total = 0
        self.last_trades_loaded_all = False

        self.session.headers.update(
            {
                "User-Agent": self.DEFAULT_USER_AGENT,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": self.BASE_URL,
                "Referer": f"{self.BASE_URL}/",
            }
        )
        apply_cookies_to_session(self.session, cookies)

    def _request_with_retries(self, method: str, url: str, **kwargs: Any) -> Any:
        request_method = getattr(self.session, method)
        kwargs.setdefault("timeout", self._timeout)
        attempts_count = self._request_retries + 1
        last_error: Exception | None = None

        for attempt_index in range(attempts_count):
            try:
                return request_method(url, **kwargs)
            except Exception as exc:
                last_error = exc
                is_last_attempt = attempt_index >= attempts_count - 1
                if is_last_attempt or not _is_retryable_request_error(exc):
                    if _is_timeout_error(exc):
                        message = _format_timeout_message(kwargs["timeout"])
                        logger.warning("Platform request timed out: %s", exc)
                        raise PlatformTimeoutError(message) from exc
                    raise
                logger.warning(
                    "Retrying platform request after %s: attempt %s/%s",
                    type(exc).__name__,
                    attempt_index + 2,
                    attempts_count,
                )
                if self._retry_backoff_seconds > 0:
                    time.sleep(self._retry_backoff_seconds * (attempt_index + 1))

        if last_error is not None:
            raise last_error
        raise RuntimeError("HTTP-запрос не был выполнен")

    def _request_trade_search(
        self,
        *,
        limit: int,
        skip: int,
        sitemap_page: str = DEFAULT_SITEMAP_PAGE,
    ) -> dict[str, Any]:
        payload = build_trade_search_payload(
            limit=limit,
            skip=skip,
            sitemap_page=sitemap_page,
        )
        response = self._request_with_retries(
            "post",
            self.url,
            json=payload,
            headers=self.headers,
        )
        if response.status_code == 403:
            raise RuntimeError("Ошибка авторизации — обновите cookies")
        response.raise_for_status()

        try:
            data = response.json()
        except ValueError:
            logger.warning("tradeSearch response is not valid JSON")
            return {"items": [], "total": 0}

        if not isinstance(data, dict):
            logger.warning("tradeSearch response is not an object: %s", type(data).__name__)
            return {"items": [], "total": 0}

        errors = data.get("errors")
        if errors:
            raise RuntimeError(f"GraphQL errors: {errors}")

        parsed = parse_trade_search_response(data)
        if not parsed["items"] and parsed["total"] == 0 and "data" not in data:
            logger.warning("tradeSearch response has no data node")
        return parsed

    def get_trades(self, limit: int = 20, skip: int = 0) -> dict[str, Any]:
        limit = self._coerce_limit(limit)
        skip = self._coerce_skip(skip)

        data = self._request_trade_search(limit=limit, skip=skip)
        items = data.get("items", [])
        if not isinstance(items, list):
            items = []

        return {
            "items": items,
            "total": normalize_total(data.get("total", 0)),
        }

    def get_trades_page(self, limit: int = 20, skip: int = 0) -> list[dict[str, Any]]:
        page = self.get_trades(limit=limit, skip=skip)
        items = page.get("items", [])
        return items if isinstance(items, list) else []

    def is_authenticated(self) -> bool:
        try:
            self.get_trades_page(limit=1, skip=0)
            return True
        except Exception:
            return False

    def get_all_trades(
        self,
        limit: int | None = None,
        max_items: int | None = None,
    ) -> list[dict[str, Any]]:
        page_limit = self._coerce_limit(limit, default=self.default_limit)
        max_items_value = self._coerce_max_items(max_items)

        all_items: list[dict[str, Any]] = []
        skip = 0
        total = 0
        limited = max_items_value > 0
        self.last_trades_total = 0
        self.last_trades_loaded_all = False

        while True:
            request_limit = self._limit_for_remaining(
                page_limit=page_limit,
                loaded_count=len(all_items),
                max_items=max_items_value,
            )
            if request_limit <= 0:
                break

            page = self.get_trades(limit=request_limit, skip=skip)
            items = page.get("items", [])
            items = items if isinstance(items, list) else []
            total = normalize_total(page.get("total", total))
            self.last_trades_total = total
            if not items:
                self.last_trades_loaded_all = True
                break

            all_items.extend(items)
            if limited and len(all_items) >= max_items_value:
                result = all_items[:max_items_value]
                self.last_trades_loaded_all = bool(total > 0 and len(result) >= total)
                return result
            if total > 0 and len(all_items) >= total:
                self.last_trades_loaded_all = True
                break
            if len(items) < request_limit and total <= 0:
                self.last_trades_loaded_all = True
                break
            skip += request_limit

        return all_items

    def load_retrades(
        self,
        limit: int | None = None,
        skip: int = 0,
        max_items: int | None = None,
    ) -> list[dict[str, Any]]:
        page_limit = self._coerce_limit(limit, default=self.default_limit)
        current_skip = self._coerce_skip(skip)
        max_items_value = self._coerce_max_items(max_items)
        limited = max_items_value > 0

        retrades: list[dict[str, Any]] = []
        total = 0

        while True:
            request_limit = self._limit_for_remaining(
                page_limit=page_limit,
                loaded_count=len(retrades),
                max_items=max_items_value,
            )
            if request_limit <= 0:
                break

            page = self._request_trade_search(
                limit=request_limit,
                skip=current_skip,
                sitemap_page=self.RETRADING_SITEMAP_PAGE,
            )
            items = page.get("items", [])
            items = items if isinstance(items, list) else []
            total = normalize_total(page.get("total", total))
            retrades.extend(parse_retrades(items))

            if limited and len(retrades) >= max_items_value:
                retrades = retrades[:max_items_value]
                break
            if total > 0 and current_skip + request_limit >= total:
                break
            if not items:
                break
            if len(items) < request_limit and total <= 0:
                break
            current_skip += request_limit

        self.retrades = retrades
        return retrades

    def get_retrading_offers(self, trade_id: int) -> list[dict[str, Any]]:
        return get_retrading_offers(self, trade_id)

    @staticmethod
    def _coerce_limit(raw_limit: Any, *, default: int = 20) -> int:
        try:
            limit = int(raw_limit)
        except (TypeError, ValueError):
            limit = default
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        return limit

    @staticmethod
    def _coerce_skip(raw_skip: Any) -> int:
        try:
            skip = int(raw_skip)
        except (TypeError, ValueError):
            skip = 0
        if skip < 0:
            raise ValueError("skip cannot be negative")
        return skip

    def _coerce_max_items(self, raw_max_items: Any) -> int:
        if raw_max_items is None:
            return self.default_max_items
        try:
            max_items = int(raw_max_items)
        except (TypeError, ValueError):
            max_items = self.default_max_items
        if max_items < 0:
            return self.default_max_items
        return max_items

    @staticmethod
    def _limit_for_remaining(
        *,
        page_limit: int,
        loaded_count: int,
        max_items: int,
    ) -> int:
        if max_items <= 0:
            return page_limit
        remaining = max_items - loaded_count
        return max(0, min(page_limit, remaining))
