from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

from config import Config
from tools import DatabaseTools as Tool

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except ModuleNotFoundError:  # pragma: no cover - dependency may be absent in test env
    PlaywrightTimeoutError = TimeoutError  # type: ignore[assignment]
    sync_playwright = None  # type: ignore[assignment]


def _normalize_cookies(raw_value: Any) -> dict[str, str]:
    if not isinstance(raw_value, dict):
        return {}
    normalized: dict[str, str] = {}
    for key, value in raw_value.items():
        key_text = str(key).strip()
        value_text = str(value).strip()
        if not key_text or not value_text:
            continue
        normalized[key_text] = value_text
    return normalized


def _resolve_config_path() -> Path:
    cfg_path = str(getattr(Config, "cfg_path", "") or "").strip()
    if cfg_path:
        return Path(cfg_path).expanduser()

    root_config = Path("config.json")
    if root_config.exists():
        return root_config

    return Path("utilities/config.json")


def save_config(data: dict) -> None:
    if not isinstance(data, dict):
        raise TypeError("save_config ожидает словарь")

    config_path = _resolve_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    payload: dict[str, Any] = {}
    if config_path.exists():
        loaded = Tool.load_json(config_path)
        if isinstance(loaded, dict):
            payload = dict(loaded)

    payload.update(data)

    cookies = _normalize_cookies(data.get("cookies"))
    if cookies:
        payload["cookies"] = cookies
        config_section = payload.get("config")
        if not isinstance(config_section, dict):
            config_section = {}
        payload["config"] = dict(config_section)
        payload["config"]["cookies"] = cookies
        if isinstance(Config.config, dict):
            Config.config["cookies"] = cookies

    Tool.save_json_atomic(config_path, payload)


class AuthService:
    BASE_URL = "https://etp.metal-it.ru"

    def __init__(self, *, headless: bool = False, timeout_ms: int = 30_000) -> None:
        self._headless = headless
        self._timeout_ms = timeout_ms

    def login_and_save_session(self, login: str, password: str) -> dict[str, str]:
        if sync_playwright is None:
            raise RuntimeError(
                "Playwright не установлен. Установите зависимость и выполните "
                "`python -m playwright install chromium`."
            )

        login_text = str(login or "").strip()
        password_text = str(password or "")
        if not login_text:
            raise ValueError("Логин не заполнен")
        if not password_text:
            raise ValueError("Пароль не заполнен")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self._headless)
            try:
                context = browser.new_context()
                page = context.new_page()

                page.goto(
                    self.BASE_URL,
                    wait_until="domcontentloaded",
                    timeout=self._timeout_ms,
                )
                page.get_by_role("button", name="Войти").first.click(timeout=self._timeout_ms)
                page.get_by_role("textbox", name="Логин").fill(login_text)
                page.get_by_role("textbox", name="Пароль").fill(password_text)
                page.get_by_role("button", name="ДАЛЕЕ").click(timeout=self._timeout_ms)

                print("Введите капчу вручную в браузере...")
                self._wait_for_login_success(page, context)

                cookies = self._extract_session_cookies(context.cookies())
                if not cookies:
                    raise RuntimeError("Не удалось получить cookies после авторизации")

                save_config({"cookies": cookies})
                return cookies
            finally:
                browser.close()

    def _wait_for_login_success(self, page, context) -> None:
        success_selector_candidates = (
            "a[href*='logout']",
            "button:has-text('Выйти')",
            "a:has-text('Выйти')",
            "button:has-text('Выход')",
            "a:has-text('Выход')",
            "button:has-text('Профиль')",
            "a:has-text('Профиль')",
        )
        success_text_candidates = (
            re.compile(r"профил", re.IGNORECASE),
            re.compile(r"выход", re.IGNORECASE),
            re.compile(r"выйти", re.IGNORECASE),
        )

        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            for selector in success_selector_candidates:
                try:
                    page.wait_for_selector(selector, state="visible", timeout=1_000)
                    return
                except PlaywrightTimeoutError:
                    continue

            for pattern in success_text_candidates:
                try:
                    page.get_by_text(pattern).first.wait_for(state="visible", timeout=1_000)
                    return
                except PlaywrightTimeoutError:
                    continue

            try:
                page.wait_for_load_state("networkidle", timeout=2_000)
            except PlaywrightTimeoutError:
                pass

            cookies = self._extract_session_cookies(context.cookies())
            if "JSESSIONID" in cookies:
                return

            page.wait_for_timeout(500)

        raise RuntimeError(
            "Не удалось подтвердить вход. Завершите капчу/2FA в браузере и повторите попытку."
        )

    @staticmethod
    def _extract_session_cookies(raw_cookies: list[dict[str, Any]]) -> dict[str, str]:
        collected: dict[str, str] = {}
        for cookie in raw_cookies:
            name = str(cookie.get("name", "")).strip()
            value = str(cookie.get("value", "")).strip()
            if not name or not value:
                continue
            collected[name] = value

        session_keys = ("JSESSIONID", "__Host-refreshToken")
        session_cookies = {key: collected[key] for key in session_keys if key in collected}
        if session_cookies:
            return session_cookies
        return collected
