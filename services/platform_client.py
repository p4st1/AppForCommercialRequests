from __future__ import annotations

from typing import Any, Mapping

import requests


class MetalITClient:
    ENDPOINT = "https://etp.metal-it.ru/api/graphql"
    _QUERY = """
    query tradeSearch($limit: Int!, $skip: Int!, $tradeQueryDto: TradeQueryDtoIn!) {
      tradeSearch(limit: $limit, skip: $skip, tradeQueryDto: $tradeQueryDto) {
        items {
          id
          title
          registeredNumber
          bidSubmissionStartDate
          bidSubmissionEndDate
          currency {
            title
          }
        }
      }
    }
    """

    def __init__(
        self,
        cookies: Mapping[str, str],
        *,
        timeout: float = 30.0,
        session: requests.Session | None = None,
    ) -> None:
        self._timeout = timeout
        self._session = session or requests.Session()
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
            }
        )
        self._session.cookies.update(dict(cookies))

    @staticmethod
    def _build_variables(limit: int, skip: int) -> dict[str, Any]:
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
                "sitemapPage": "purchases.trades.filters.BID_SUBMISSION",
            },
        }

    def _request_trade_search(self, *, limit: int, skip: int) -> dict[str, Any]:
        payload = {
            "operationName": "tradeSearch",
            "variables": self._build_variables(limit=limit, skip=skip),
            "query": self._QUERY,
        }
        response = self._session.post(self.ENDPOINT, json=payload, timeout=self._timeout)
        response.raise_for_status()
        response_payload = response.json()
        if "data" not in response_payload:
            raise Exception(f"GraphQL response does not contain 'data': {response_payload}")
        if response_payload.get("errors"):
            raise Exception(f"GraphQL returned errors: {response_payload['errors']}")
        data = response_payload["data"]
        if not isinstance(data, Mapping):
            raise Exception(f"Unexpected GraphQL data format: {data}")
        return dict(data)

    @staticmethod
    def _extract_items(data: Mapping[str, Any]) -> list[dict[str, Any]]:
        trade_search = data.get("tradeSearch")
        if trade_search is None:
            return []
        if isinstance(trade_search, list):
            return [item for item in trade_search if isinstance(item, dict)]
        if isinstance(trade_search, Mapping):
            items = trade_search.get("items", [])
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
        return []

    def get_trades_page(self, limit: int = 20, skip: int = 0) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        if skip < 0:
            raise ValueError("skip cannot be negative")

        data = self._request_trade_search(limit=limit, skip=skip)
        items = self._extract_items(data)
        print(f"Загружено заявок: {len(items)} (skip={skip}, limit={limit})")
        return items

    def get_all_trades(self, limit: int = 20) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        all_items: list[dict[str, Any]] = []
        skip = 0

        while True:
            items = self.get_trades_page(limit=limit, skip=skip)
            if not items:
                break
            all_items.extend(items)
            skip += limit

        print(f"Загружено заявок всего: {len(all_items)}")
        return all_items


if __name__ == "__main__":
    cookies = {
        "JSESSIONID": "PUT_YOUR_VALUE",
    }

    client = MetalITClient(cookies)
    trades = client.get_all_trades()
    print(len(trades))
