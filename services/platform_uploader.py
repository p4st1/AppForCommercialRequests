from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


class TradeUploader:
    BASE_URL = "https://etp.metal-it.ru"
    TRADE_URL_TEMPLATE = "https://etp.metal-it.ru/trades/{trade_id}"

    def __init__(
        self,
        cookies: dict[str, str],
        *,
        headless: bool = False,
        timeout_ms: int = 30_000,
    ) -> None:
        self._cookies = self._normalize_cookies(cookies)
        if not self._cookies:
            raise ValueError("Не найдены cookies для авторизации в config.json")
        self._headless = headless
        self._timeout_ms = timeout_ms

    @staticmethod
    def _normalize_cookies(raw: Any) -> dict[str, str]:
        if not isinstance(raw, dict):
            return {}
        result: dict[str, str] = {}
        for key, value in raw.items():
            key_text = str(key).strip()
            value_text = str(value).strip()
            if not key_text or not value_text:
                continue
            result[key_text] = value_text
        return result

    def _build_playwright_cookies(self) -> list[dict[str, str]]:
        return [
            {
                "name": name,
                "value": value,
                "url": self.BASE_URL,
            }
            for name, value in self._cookies.items()
        ]

    def upload_file(self, trade_id: int, file_path: str) -> str:
        try:
            trade_id_int = int(trade_id)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Некорректный trade_id: {trade_id}") from exc
        if trade_id_int <= 0:
            raise ValueError(f"trade_id должен быть положительным числом: {trade_id_int}")

        candidate_path = Path(file_path).expanduser()
        if not candidate_path.exists() or not candidate_path.is_file():
            raise FileNotFoundError(f"Excel файл не найден: {candidate_path}")
        if candidate_path.suffix.lower() not in {".xlsx", ".xls"}:
            raise ValueError(f"Поддерживаются только .xls/.xlsx: {candidate_path}")

        resolved_path = candidate_path.resolve()
        trade_url = self.TRADE_URL_TEMPLATE.format(trade_id=trade_id_int)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self._headless)
            try:
                context = browser.new_context()
                context.add_cookies(self._build_playwright_cookies())
                page = context.new_page()

                page.goto(self.BASE_URL, wait_until="domcontentloaded", timeout=self._timeout_ms)
                page.goto(trade_url, wait_until="domcontentloaded", timeout=self._timeout_ms)

                page.wait_for_selector("input[type=file]", timeout=self._timeout_ms)
                page.set_input_files("input[type=file]", str(resolved_path))

                self._click_submit_button(page)
                self._wait_for_upload_confirmation(page)
            finally:
                browser.close()

        return f"Файл '{resolved_path.name}' загружен в заявку {trade_id_int}"

    def _click_submit_button(self, page: Page) -> None:
        button_names = (
            "Загрузить",
            "Отправить",
            "Загрузить КП",
            "Отправить КП",
        )
        for name in button_names:
            try:
                page.get_by_role("button", name=name).first.click(timeout=4_000)
                return
            except Exception:
                continue

        fallback_patterns = (
            re.compile(r"загруз", re.IGNORECASE),
            re.compile(r"отправ", re.IGNORECASE),
        )
        for pattern in fallback_patterns:
            try:
                page.get_by_role("button", name=pattern).first.click(timeout=4_000)
                return
            except Exception:
                continue

        raise RuntimeError(
            "Не удалось найти кнопку загрузки на странице заявки "
            "(ожидались кнопки 'Загрузить' или 'Отправить')."
        )

    def _wait_for_upload_confirmation(self, page: Page) -> None:
        try:
            page.wait_for_load_state("networkidle", timeout=10_000)
        except PlaywrightTimeoutError:
            pass

        success_patterns = (
            re.compile(r"успеш", re.IGNORECASE),
            re.compile(r"загруж", re.IGNORECASE),
            re.compile(r"отправ", re.IGNORECASE),
            re.compile(r"добавлен", re.IGNORECASE),
        )
        for pattern in success_patterns:
            try:
                page.get_by_text(pattern).first.wait_for(state="visible", timeout=4_000)
                return
            except PlaywrightTimeoutError:
                continue

        error_patterns = (
            re.compile(r"ошиб", re.IGNORECASE),
            re.compile(r"не удалось", re.IGNORECASE),
        )
        for pattern in error_patterns:
            try:
                locator = page.get_by_text(pattern).first
                if locator.is_visible(timeout=1_500):
                    raise RuntimeError(f"Площадка вернула ошибку: {locator.inner_text().strip()}")
            except PlaywrightTimeoutError:
                continue

        raise RuntimeError(
            "Не удалось подтвердить загрузку файла: на странице не найдено сообщение об успехе."
        )
