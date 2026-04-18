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
    ENDPOINT = "https://etp.metal-it.ru/graphql/tradeSearch"

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
        self.url = self.ENDPOINT
        raw_cookies = dict(cookies)
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://etp.metal-it.ru",
                "Referer": "https://etp.metal-it.ru/",
                "X-XSRF-TOKEN": str(raw_cookies.get("XSRF-TOKEN", "")),
            }
        )
        for key, value in raw_cookies.items():
            self.session.cookies.set(str(key), str(value))

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

    def _request_trade_search(self, *, limit: int, skip: int) -> list[dict[str, Any]]:
        payload = {
            "operationName": "tradeSearch",
            "variables": self._build_variables(limit=limit, skip=skip),
            "query": FULL_GRAPHQL_QUERY,
        }
        response = self.session.post(
            self.url,
            json=payload,
            timeout=self._timeout,
        )
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text[:500])
        response.raise_for_status()
        data = response.json()
        if "data" not in data:
            raise Exception(f"GraphQL response does not contain 'data': {data}")
        return data["data"]["trades"]["items"]

    def get_trades_page(self, limit: int = 20, skip: int = 0) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        if skip < 0:
            raise ValueError("skip cannot be negative")

        items = self._request_trade_search(limit=limit, skip=skip)
        print(f"Загружено заявок: {len(items)} (skip={skip}, limit={limit})")
        return items

    def is_authenticated(self) -> bool:
        try:
            self.get_trades_page(limit=1, skip=0)
            return True
        except Exception as exc:
            if "401" in str(exc):
                return False
            return False

    def get_all_trades(self, limit: int = 20, max_items: int = 100) -> list[dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        all_items: list[dict[str, Any]] = []
        skip = 0

        while True:
            items = self.get_trades_page(limit=limit, skip=skip)
            if not items:
                break
            all_items.extend(items)
            if len(all_items) >= max_items:
                return all_items[:max_items]
            skip += limit

        print(f"Загружено заявок всего: {len(all_items)}")
        return all_items


if __name__ == "__main__":
    cookies = {
        "JSESSIONID": "46052C544D1BE9D019A2EE099B42C01F",
    }

    client = MetalITClient(cookies)
    trades = client.get_all_trades()
    print(len(trades))
