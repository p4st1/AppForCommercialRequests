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
      organizer {
        title
      }
      procurementMethod {
        title
      }
      bidSubmissionEndDate
      processStatus
      lots {
        id
        title
        biddingData {
          bidSubmissionEndDate
        }
      }
    }
    total
  }
}
"""


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
                "X-XSRF-TOKEN": str(cookies_with_aliases.get("XSRF-TOKEN", "")),
            }
        )
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
        print("COOKIES:", self.session.cookies.get_dict())
        print("HEADERS:", dict(self.session.headers))
        response = self.session.post(
            self.url,
            json=payload,
            headers=self.headers,
            timeout=self._timeout,
        )
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text[:500])
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
        print(f"Загружено заявок: {len(items)} (skip={skip}, limit={limit}, total={total})")
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

    def get_all_trades(self, limit: int = 20, max_items: int = 100) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        all_items: list[dict[str, Any]] = []
        skip = 0
        total = 0

        while True:
            page = self.get_trades(limit=limit, skip=skip)
            items = page.get("items", [])
            total = self._normalize_total(page.get("total", total))
            if not items:
                break
            all_items.extend(items)
            if len(all_items) >= max_items:
                return all_items[:max_items]
            if total > 0 and skip + limit >= total:
                break
            if len(items) < limit and total <= 0:
                break
            skip += limit

        print(f"Загружено заявок всего: {len(all_items)}")
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
                print(message)
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
                retrades.append(
                    {
                        "id": trade.get("id"),
                        "number": trade.get("registeredNumber"),
                        "title": trade.get("title"),
                        "status": trade.get("processStatus"),
                        "endDate": trade.get("bidSubmissionEndDate"),
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
        print(f"Загружено переторжек: {len(retrades)}")
        return retrades


if __name__ == "__main__":
    cookies = {
        "JSESSIONID": "46052C544D1BE9D019A2EE099B42C01F",
    }

    client = MetalITClient(cookies)
    trades = client.get_all_trades()
    print(len(trades))
