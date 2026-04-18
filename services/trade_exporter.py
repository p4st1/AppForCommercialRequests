from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import requests
from playwright.sync_api import Locator, Page, sync_playwright

from config import Config
from tools import DatabaseTools as Tool


class TradeExporter:
    BASE_URL = "https://etp.metal-it.ru"
    TRADE_SEARCH_ENDPOINT = "https://etp.metal-it.ru/graphql/tradeSearch"
    TRADE_SEARCH_QUERY = """
query tradeSearch($tradeQueryDto: TradeQueryDtoInput, $limit: Int, $skip: Int) {
  trades(tradeQueryDto: $tradeQueryDto, limit: $limit, skip: $skip) {
    items {
      id
      lots {
        id
      }
    }
  }
}
"""

    def __init__(self, *, headless: bool = True, timeout_ms: int = 30_000) -> None:
        self._headless = headless
        self._timeout_ms = timeout_ms

    @staticmethod
    def _normalize_cookies(raw_value: Any) -> dict[str, str]:
        if not isinstance(raw_value, dict):
            return {}
        return {
            str(key): str(value)
            for key, value in raw_value.items()
            if str(key).strip() and str(value).strip()
        }

    def _extract_cookies_from_payload(self, payload: dict[str, Any]) -> dict[str, str]:
        candidates: list[Any] = [payload.get("cookies")]

        config_section = payload.get("config")
        if isinstance(config_section, dict):
            candidates.append(config_section.get("cookies"))
            platform_section = config_section.get("platform")
            if isinstance(platform_section, dict):
                candidates.append(platform_section.get("cookies"))

        platform_root = payload.get("platform")
        if isinstance(platform_root, dict):
            candidates.append(platform_root.get("cookies"))

        for candidate in candidates:
            normalized = self._normalize_cookies(candidate)
            if normalized:
                return normalized

        return {}

    def _load_cookies_from_config(self) -> dict[str, str]:
        candidate_paths: list[Path] = []

        cfg_path = str(getattr(Config, "cfg_path", "") or "").strip()
        if cfg_path:
            candidate_paths.append(Path(cfg_path))

        candidate_paths.extend(
            [
                Path("config.json"),
                Path("utilities/config.json"),
            ]
        )

        seen: set[Path] = set()
        errors: list[str] = []

        for path in candidate_paths:
            resolved_path = path.expanduser()
            if resolved_path in seen:
                continue
            seen.add(resolved_path)

            if not resolved_path.exists():
                continue

            try:
                payload = Tool.load_json(resolved_path)
            except Exception as exc:
                errors.append(f"{resolved_path}: {exc}")
                continue

            cookies = self._extract_cookies_from_payload(payload)
            if cookies:
                return cookies

            errors.append(
                f"{resolved_path}: не найден раздел 'cookies' "
                "(поддерживаются: cookies, config.cookies, config.platform.cookies)"
            )

        if errors:
            raise ValueError("; ".join(errors))
        raise FileNotFoundError("Не найден config.json с cookies")

    @classmethod
    def _build_playwright_cookies(cls, cookies: dict[str, str]) -> list[dict[str, str]]:
        return [
            {
                "name": name,
                "value": value,
                "url": cls.BASE_URL,
            }
            for name, value in cookies.items()
        ]

    @staticmethod
    def _build_trade_search_variables(limit: int, skip: int) -> dict[str, Any]:
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

    @classmethod
    def _build_api_session(cls, cookies: dict[str, str]) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": cls.BASE_URL,
                "Referer": f"{cls.BASE_URL}/",
                "X-XSRF-TOKEN": str(cookies.get("XSRF-TOKEN", "")),
            }
        )
        for key, value in cookies.items():
            session.cookies.set(str(key), str(value))
        return session

    def _request_trade_page(
        self,
        *,
        session: requests.Session,
        limit: int,
        skip: int,
    ) -> list[dict[str, Any]]:
        payload = {
            "operationName": "tradeSearch",
            "variables": self._build_trade_search_variables(limit=limit, skip=skip),
            "query": self.TRADE_SEARCH_QUERY,
        }
        response = session.post(
            self.TRADE_SEARCH_ENDPOINT,
            json=payload,
            timeout=max(10.0, self._timeout_ms / 1000),
        )
        response.raise_for_status()
        body = response.json()

        data = body.get("data", {})
        trades = data.get("trades", {})
        items = trades.get("items", [])
        return items if isinstance(items, list) else []

    @staticmethod
    def _parse_lot_id(trade: dict[str, Any], trade_id: int) -> int:
        lots = trade.get("lots")
        if not isinstance(lots, list) or not lots:
            raise ValueError(f"У заявки {trade_id} отсутствуют лоты")
        first_lot = lots[0]
        if not isinstance(first_lot, dict):
            raise ValueError(f"Не удалось получить lot_id для заявки {trade_id}")

        lot_id_raw = first_lot.get("id")
        try:
            lot_id = int(lot_id_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Некорректный lot_id для заявки {trade_id}: {lot_id_raw}"
            ) from exc
        if lot_id <= 0:
            raise ValueError(f"Некорректный lot_id для заявки {trade_id}: {lot_id}")
        return lot_id

    def _resolve_lot_id_from_api(self, trade_id: int, cookies: dict[str, str]) -> int:
        limit = 100
        max_pages = 20
        session = self._build_api_session(cookies)

        try:
            for page_index in range(max_pages):
                skip = page_index * limit
                items = self._request_trade_page(session=session, limit=limit, skip=skip)
                if not items:
                    break

                for trade in items:
                    if not isinstance(trade, dict):
                        continue
                    trade_raw_id = trade.get("id")
                    try:
                        current_trade_id = int(trade_raw_id)
                    except (TypeError, ValueError):
                        continue
                    if current_trade_id != trade_id:
                        continue
                    return self._parse_lot_id(trade, trade_id)

                if len(items) < limit:
                    break
        finally:
            session.close()

        raise ValueError(f"Заявка {trade_id} не найдена в API или недоступна для подачи")

    @staticmethod
    def _click_with_log(locator: Locator, *, button_text: str, timeout_ms: int) -> None:
        print("CLICK:", button_text)
        locator.click(timeout=timeout_ms)

    def _resolve_export_button(self, page: Page) -> Locator:
        specification_block = page.locator("section, article, div").filter(
            has_text=re.compile(r"Спецификац", re.IGNORECASE)
        )
        search_roots: list[Page | Locator] = [page]
        if specification_block.count() > 0:
            search_roots.insert(0, specification_block.first)

        selectors: tuple[str, ...] = (
            "button[aria-label*='Экспорт']",
            "button[data-testid*='export']",
            "button[data-testid*='Export']",
            "button[data-testid*='Экспорт']",
            "button:has-text('Экспорт')",
        )
        for root in search_roots:
            for selector in selectors:
                button = root.locator(selector)
                button_count = button.count()
                if button_count == 1:
                    return button.first

        fallback = page.get_by_role("button", name="Экспорт")
        fallback_count = fallback.count()
        if fallback_count == 1:
            return fallback.first
        if fallback_count > 1:
            raise RuntimeError("Найдено несколько кнопок 'Экспорт'. Уточните селектор.")
        raise RuntimeError("Не удалось найти кнопку 'Экспорт' в блоке 'Спецификация'.")

    def export_trade_data(self, trade_id: int, download_path: str) -> str:
        try:
            trade_id_int = int(trade_id)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Некорректный trade_id: {trade_id}") from exc
        if trade_id_int <= 0:
            raise ValueError(f"trade_id должен быть положительным числом: {trade_id_int}")

        target_path = Path(download_path).expanduser()
        if target_path.suffix.lower() not in {".xlsx", ".xls"}:
            raise ValueError("Файл экспорта должен иметь расширение .xlsx или .xls")
        target_path.parent.mkdir(parents=True, exist_ok=True)

        cookies = self._load_cookies_from_config()
        if not cookies:
            raise ValueError("Не найдены cookies для авторизации в config.json")

        lot_id = self._resolve_lot_id_from_api(trade_id=trade_id_int, cookies=cookies)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self._headless)
            try:
                context = browser.new_context(accept_downloads=True)
                context.add_cookies(self._build_playwright_cookies(cookies))
                page = context.new_page()

                page.goto(
                    f"https://etp.metal-it.ru/bids/new?lot={lot_id}",
                    wait_until="domcontentloaded",
                    timeout=self._timeout_ms,
                )
                page.wait_for_load_state("domcontentloaded", timeout=self._timeout_ms)
                page.wait_for_selector("text=Экспорт", timeout=30_000)
                export_button = self._resolve_export_button(page)

                with page.expect_download(timeout=self._timeout_ms) as download_info:
                    self._click_with_log(
                        export_button,
                        button_text="Экспорт",
                        timeout_ms=self._timeout_ms,
                    )

                download = download_info.value
                download.save_as(str(target_path))
            finally:
                browser.close()

        return str(target_path.resolve())

    def export_trade(self, trade_id: int, download_path: str) -> str:
        return self.export_trade_data(trade_id=trade_id, download_path=download_path)
