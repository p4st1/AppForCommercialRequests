from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


class TradeUploader:
    BASE_URL = "https://etp.metal-it.ru"
    TRADE_URL_TEMPLATE = "https://etp.metal-it.ru/trades/{trade_id}"
    SUBMIT_BUTTON_TEXT = "Подать предложение"

    def __init__(
        self,
        cookies: dict[str, str],
        *,
        headless: bool = False,
        allow_submit: bool = False,
        timeout_ms: int = 30_000,
    ) -> None:
        self._cookies = self._normalize_cookies(cookies)
        if not self._cookies:
            raise ValueError("Не найдены cookies для авторизации в config.json")
        self._headless = headless
        self._allow_submit = bool(allow_submit)
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
        return self.submit_trade(trade_id=trade_id, file_path=file_path)

    def submit_trade(
        self,
        trade_id: int,
        file_path: str,
        *,
        allow_submit: bool | None = None,
    ) -> str:
        submit_allowed = self._allow_submit if allow_submit is None else bool(allow_submit)
        if not submit_allowed:
            raise PermissionError(
                "Отправка КП заблокирована: allow_submit=False. "
                "Подтвердите действие в интерфейсе перед отправкой."
            )

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

                self._click_upload_button(page)
                self._click_submit_button(page)
                self._wait_for_upload_confirmation(page)
            finally:
                browser.close()

        return f"Файл '{resolved_path.name}' загружен в заявку {trade_id_int}"

    def _click_with_log(self, locator: Locator, *, button_text: str, timeout_ms: int) -> None:
        print("CLICK:", button_text)
        locator.click(timeout=timeout_ms)

    def _click_upload_button(self, page: Page) -> None:
        button_candidates: tuple[tuple[str, str], ...] = (
            ("button[aria-label*='Загрузить']", "Загрузить"),
            ("button[data-testid*='upload']", "Загрузить"),
            ("button[data-testid*='Upload']", "Загрузить"),
            ("button:has-text('Загрузить КП')", "Загрузить КП"),
            ("button:has-text('Загрузить')", "Загрузить"),
        )
        ambiguous_selectors: list[str] = []
        for selector, button_text in button_candidates:
            locator = page.locator(selector)
            count = locator.count()
            if count == 0:
                continue
            if count > 1:
                ambiguous_selectors.append(selector)
                continue
            self._click_with_log(locator.first, button_text=button_text, timeout_ms=4_000)
            return

        if ambiguous_selectors:
            raise RuntimeError(
                "Не удалось однозначно выбрать кнопку загрузки файла. "
                f"Неоднозначные селекторы: {', '.join(ambiguous_selectors)}"
            )

    def _click_submit_button(self, page: Page) -> None:
        btn = page.locator(f"button:has-text('{self.SUBMIT_BUTTON_TEXT}')")
        button_count = btn.count()
        if button_count == 0:
            raise RuntimeError(
                "Не найдена финальная кнопка отправки 'Подать предложение'. "
                "Проверьте верстку страницы."
            )
        if button_count > 1:
            raise RuntimeError(
                "Найдено несколько кнопок 'Подать предложение'. "
                "Отправка остановлена из соображений безопасности."
            )
        self._click_with_log(btn.first, button_text=self.SUBMIT_BUTTON_TEXT, timeout_ms=4_000)

    def _wait_for_upload_confirmation(self, page: Page) -> None:
        try:
            page.wait_for_load_state("networkidle", timeout=10_000)
        except PlaywrightTimeoutError:
            pass

        success_patterns = (
            re.compile(r"успеш", re.IGNORECASE),
            re.compile(r"загруж", re.IGNORECASE),
            re.compile(r"отправ", re.IGNORECASE),
            re.compile(r"предложени.*подан", re.IGNORECASE),
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
