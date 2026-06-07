from __future__ import annotations

from typing import Any

from services.platform.constants import DEFAULT_SITEMAP_PAGE


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


def build_trade_search_variables(
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


def build_trade_search_payload(
    *,
    limit: int,
    skip: int,
    sitemap_page: str = DEFAULT_SITEMAP_PAGE,
) -> dict[str, Any]:
    return {
        "operationName": "tradeSearch",
        "variables": build_trade_search_variables(
            limit=limit,
            skip=skip,
            sitemap_page=sitemap_page,
        ),
        "query": FULL_GRAPHQL_QUERY,
    }
