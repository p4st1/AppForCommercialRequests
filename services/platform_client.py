from __future__ import annotations

from typing import Any

import requests

FULL_GRAPHQL_QUERY = """
query tradeSearch($tradeQueryDto: TradeQueryDtoInput, $limit: Int, $skip: Int) {
  trades(tradeQueryDto: $tradeQueryDto, limit: $limit, skip: $skip) {
    items {
      id
      registeredNumber
      title
      processStatus
      currentStage {
        id
      }
      organizer {
        title
      }
      customer {
        title
      }
      currency {
        title
      }
      lots {
        id
      }
    }
    total
  }
}
"""
TRADE_DETAILS_ENDPOINT_PATTERN = "{base_url}/trades/{trade_id}"


def _normalize_trade_json(raw_payload: Any) -> dict[str, Any]:
    if not isinstance(raw_payload, dict):
        return {}
    if isinstance(raw_payload.get("submissionStages"), list):
        return raw_payload

    data_node = raw_payload.get("data")
    if isinstance(data_node, dict):
        if isinstance(data_node.get("submissionStages"), list):
            return data_node
        trade_node = data_node.get("trade")
        if isinstance(trade_node, dict) and isinstance(trade_node.get("submissionStages"), list):
            return trade_node

    trade_node = raw_payload.get("trade")
    if isinstance(trade_node, dict) and isinstance(trade_node.get("submissionStages"), list):
        return trade_node

    return raw_payload


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
    timeout = float(getattr(platform_client, "_timeout", 30.0) or 30.0)
    base_url = str(getattr(platform_client, "BASE_URL", "https://etp.metal-it.ru"))

    endpoint = TRADE_DETAILS_ENDPOINT_PATTERN.format(
        base_url=base_url.rstrip("/"),
        trade_id=trade_id_int,
    )
    response = session.get(
        endpoint,
        headers=headers,
        timeout=timeout,
    )
    if response.status_code == 403:
        raise RuntimeError("Ошибка авторизации — обновите cookies")
    response.raise_for_status()

    body = response.json()
    return _normalize_trade_json(body)


def parse_retrade_bids(trade_json: dict) -> list[dict]:
    normalized_trade = _normalize_trade_json(trade_json)

    stages = normalized_trade.get("submissionStages", [])
    if not isinstance(stages, list):
        stages = []

    bids: list[dict[str, Any]] = []
    seen_bid_ids: set[int] = set()

    for stage in stages:
        if not isinstance(stage, dict):
            continue
        trade_result = stage.get("tradeResult")
        if not isinstance(trade_result, dict):
            continue

        lot_results = trade_result.get("lotResults", [])
        if not isinstance(lot_results, list):
            lot_results = []

        for lot in lot_results:
            if not isinstance(lot, dict):
                continue
            bid_places = lot.get("bidPlaces", [])
            if not isinstance(bid_places, list):
                bid_places = []

            for place in bid_places:
                if not isinstance(place, dict):
                    continue
                bid = place.get("bid")
                if not isinstance(bid, dict):
                    continue

                bid_id_raw = bid.get("id")
                try:
                    bid_id = int(bid_id_raw)
                except (TypeError, ValueError):
                    continue
                if bid_id <= 0 or bid_id in seen_bid_ids:
                    continue

                status_node = bid.get("status")
                status_title = ""
                if isinstance(status_node, dict):
                    status_title = str(status_node.get("title", "") or "")

                bidder_node = bid.get("bidder")
                bidder_title = ""
                if isinstance(bidder_node, dict):
                    bidder_title = str(bidder_node.get("title", "") or "")

                parsed_bid = {
                    "bid_id": bid_id,
                    "number": str(bid.get("number", "") or ""),
                    "price": bid.get("price"),
                    "status": status_title,
                    "bid_date": bid.get("bidDate"),
                    "bidder_title": bidder_title,
                }
                bids.append(parsed_bid)
                seen_bid_ids.add(bid_id)

    return bids


def get_retrading_offers(platform_client: Any, trade_id: int) -> list[dict]:
    trade_json = get_trade_json(platform_client, trade_id)
    return parse_retrade_bids(trade_json)


class MetalITClient:
    BASE_URL = "https://etp.metal-it.ru"
    ENDPOINT = "https://etp.metal-it.ru/graphql/tradeSearch"
    DEFAULT_SITEMAP_PAGE = "purchases.trades.filters.BID_SUBMISSION"
    RETRADING_SITEMAP_PAGE = "purchases.trades.filters.RETRADING"
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        cookies: dict[str, str],
        *,
        timeout: float = 30.0,
        session: requests.Session | None = None,
    ) -> None:
        self._timeout = timeout
        self._session = session or requests.Session()
        self.session = self._session
        self.headers = self.session.headers
        self.url = self.ENDPOINT
        self.retrades: list[dict[str, Any]] = []
        self.last_trades_total = 0
        self.last_trades_loaded_all = False
        normalized_cookies = self._normalize_cookies(cookies)
        cookies_with_aliases = self._with_session_cookie_aliases(normalized_cookies)
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
        xsrf_token = str(cookies_with_aliases.get("XSRF-TOKEN", "") or "").strip()
        if xsrf_token:
            self.session.headers["X-XSRF-TOKEN"] = xsrf_token
        for key, value in cookies_with_aliases.items():
            key_text = str(key).strip()
            value_text = str(value).strip()
            if not key_text or not value_text:
                continue
            self.session.cookies.set(
                key_text,
                value_text,
                domain="etp.metal-it.ru",
                path="/",
            )
            self.session.cookies.set(key_text, value_text)

    @staticmethod
    def _normalize_cookies(raw: Any) -> dict[str, str]:
        if not isinstance(raw, dict):
            return {}
        return {
            str(key): str(value)
            for key, value in raw.items()
            if str(key).strip() and str(value).strip()
        }

    @staticmethod
    def _with_session_cookie_aliases(cookies: dict[str, str]) -> dict[str, str]:
        normalized = dict(cookies)
        jsession = str(normalized.get("JSESSIONID", "") or "").strip()
        host_jsession = str(normalized.get("__Host-JSESSIONID", "") or "").strip()
        if jsession and not host_jsession:
            normalized["__Host-JSESSIONID"] = jsession
        if host_jsession and not jsession:
            normalized["JSESSIONID"] = host_jsession
        return normalized

    @staticmethod
    def _build_variables(
        limit: int,
        skip: int,
        *,
        sitemap_page: str = DEFAULT_SITEMAP_PAGE,
    ) -> dict[str, Any]:
        return {
            "limit": limit,
            "skip": skip,
            "tradeQueryDto": {
                "order": {
                    "expressions": [
                        {"ascending": False, "property": "REGISTERED_DATE"},
                        {"ascending": False, "property": "ID"},
                    ]
                },
                "sitemapPage": sitemap_page,
            },
        }

    @staticmethod
    def _normalize_total(raw_total: Any) -> int:
        try:
            normalized_total = int(raw_total)
        except (TypeError, ValueError):
            return 0
        return max(0, normalized_total)

    def _request_trade_search(
        self,
        *,
        limit: int,
        skip: int,
        sitemap_page: str = DEFAULT_SITEMAP_PAGE,
    ) -> dict[str, Any]:
        payload = {
            "operationName": "tradeSearch",
            "variables": self._build_variables(
                limit=limit,
                skip=skip,
                sitemap_page=sitemap_page,
            ),
            "query": FULL_GRAPHQL_QUERY,
        }
        response = self.session.post(
            self.url,
            json=payload,
            headers=self.headers,
            timeout=self._timeout,
        )
        response.raise_for_status()
        data = response.json()
        errors = data.get("errors")
        if errors:
            raise RuntimeError(f"GraphQL errors: {errors}")
        if "data" not in data:
            raise Exception(f"GraphQL response does not contain 'data': {data}")
        data_root = data.get("data")
        if not isinstance(data_root, dict):
            raise RuntimeError(f"Некорректный формат GraphQL data: {type(data_root).__name__}")
        trades = data_root.get("trades", {})
        if not isinstance(trades, dict):
            raise RuntimeError("GraphQL payload не содержит объект trades")
        items = trades.get("items", [])
        if not isinstance(items, list):
            raise RuntimeError("GraphQL payload не содержит список trades.items")
        total = self._normalize_total(trades.get("total", 0))
        return {
            "items": items,
            "total": total,
        }

    def get_trades(self, limit: int = 20, skip: int = 0) -> dict[str, Any]:
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        if skip < 0:
            raise ValueError("skip cannot be negative")

        data = self._request_trade_search(limit=limit, skip=skip)
        items = data.get("items", [])
        if not isinstance(items, list):
            raise RuntimeError("Некорректный формат items в ответе tradeSearch")

        total = self._normalize_total(data.get("total", 0))
        return {
            "items": items,
            "total": total,
        }

    def get_trades_page(self, limit: int = 20, skip: int = 0) -> list[dict[str, Any]]:
        page = self.get_trades(limit=limit, skip=skip)
        items = page.get("items", [])
        if not isinstance(items, list):
            raise RuntimeError("Некорректный формат items в ответе tradeSearch")
        return items

    def is_authenticated(self) -> bool:
        try:
            self.get_trades_page(limit=1, skip=0)
            return True
        except Exception as exc:
            if "401" in str(exc) or "403" in str(exc):
                return False
            return False

    def get_all_trades(self, limit: int = 100, max_items: int = 100) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        if max_items < 0:
            max_items = 100

        all_items: list[dict[str, Any]] = []
        skip = 0
        total = 0
        limited = max_items > 0
        self.last_trades_total = 0
        self.last_trades_loaded_all = False

        while True:
            page = self.get_trades(limit=limit, skip=skip)
            items = page.get("items", [])
            total = self._normalize_total(page.get("total", total))
            self.last_trades_total = total
            if not items:
                self.last_trades_loaded_all = True
                break
            all_items.extend(items)
            if limited and len(all_items) >= max_items:
                result = all_items[:max_items]
                self.last_trades_loaded_all = bool(total > 0 and len(result) >= total)
                return result
            if total > 0 and len(all_items) >= total:
                self.last_trades_loaded_all = True
                break
            if len(items) < limit and total <= 0:
                self.last_trades_loaded_all = True
                break
            skip += limit

        return all_items

    def load_retrades(self, limit: int = 50, skip: int = 0) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        if skip < 0:
            raise ValueError("skip cannot be negative")

        retrades: list[dict[str, Any]] = []
        current_skip = skip
        total = 0

        while True:
            payload = {
                "operationName": "tradeSearch",
                "variables": self._build_variables(
                    limit=limit,
                    skip=current_skip,
                    sitemap_page=self.RETRADING_SITEMAP_PAGE,
                ),
                "query": FULL_GRAPHQL_QUERY,
            }
            response = self.session.post(
                self.url,
                json=payload,
                headers=self.headers,
                timeout=self._timeout,
            )
            if response.status_code == 403:
                message = "Ошибка авторизации — обновите cookies"
                raise RuntimeError(message)

            response.raise_for_status()
            data = response.json()

            errors = data.get("errors")
            if errors:
                raise RuntimeError(f"GraphQL errors: {errors}")

            try:
                trades_payload = data["data"]["trades"]
                items = trades_payload["items"]
            except (TypeError, KeyError) as exc:
                raise RuntimeError("Некорректный формат ответа tradeSearch") from exc

            if not isinstance(items, list):
                raise RuntimeError("Некорректный формат items в ответе tradeSearch")

            total = self._normalize_total(trades_payload.get("total", total))
            for trade in items:
                if not isinstance(trade, dict):
                    continue

                lots_raw = trade.get("lots")
                lots = lots_raw if isinstance(lots_raw, list) else []
                first_lot = lots[0] if lots and isinstance(lots[0], dict) else {}
                lot_id = first_lot.get("id")
                retrades.append(
                    {
                        "id": trade.get("id"),
                        "stage_id": (
                            trade.get("currentStage", {}).get("id")
                            if isinstance(trade.get("currentStage"), dict)
                            else None
                        ),
                        "number": trade.get("registeredNumber"),
                        "title": trade.get("title"),
                        "status": trade.get("processStatus"),
                        "endDate": trade.get("bidSubmissionEndDate") or "",
                        "lot_id": lot_id,
                        "lots": lots,
                        "organizer": trade.get("organizer"),
                        "customer": trade.get("customer"),
                        "currency": trade.get("currency"),
                    }
                )

            if total > 0 and current_skip + limit >= total:
                break
            if not items:
                break
            if len(items) < limit and total <= 0:
                break
            current_skip += limit

        self.retrades = retrades
        return retrades

    def get_retrading_offers(self, trade_id: int) -> list[dict[str, Any]]:
        return get_retrading_offers(self, trade_id)
