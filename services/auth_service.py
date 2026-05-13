from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import requests
except ModuleNotFoundError:  # pragma: no cover - dependency may be absent in test env
    requests = None  # type: ignore[assignment]

from config import Config
from tools import DatabaseTools as Tool

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except (ImportError, ModuleNotFoundError):  # pragma: no cover - dependency may be absent in test env
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

    return Tool.user_config_path()


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
    TRADES_URL = f"{BASE_URL}/trades"
    TRADE_SEARCH_ENDPOINT = f"{BASE_URL}/graphql/tradeSearch"
    LOGIN_SUCCESS_SELECTOR = "text=Приём заявок"
    CAPTCHA_WAIT_TIMEOUT_MS = 120_000
    POST_LOGIN_SETTLE_TIMEOUT_MS = 3_000

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
                self._wait_for_login_success(page)
                page.wait_for_timeout(self.POST_LOGIN_SETTLE_TIMEOUT_MS)

                page.goto(
                    self.TRADES_URL,
                    wait_until="domcontentloaded",
                    timeout=self._timeout_ms,
                )
                page.wait_for_timeout(self.POST_LOGIN_SETTLE_TIMEOUT_MS)

                cookies = self._extract_session_cookies(context.cookies())
                if not cookies:
                    raise RuntimeError("Не удалось получить cookies после авторизации")
                print("Cookies после авторизации:", list(cookies.keys()))

                has_host_session = "__Host-JSESSIONID" in cookies
                has_session = "JSESSIONID" in cookies
                if not has_host_session and not has_session:
                    is_api_ok = self._is_trade_search_available(cookies)
                    if not is_api_ok:
                        raise RuntimeError(
                            "После авторизации не найдены session cookies "
                            "(__Host-JSESSIONID/JSESSIONID) и API недоступно"
                        )

                save_config({"cookies": cookies})
                self._save_cookies_to_root_config(cookies)
                return cookies
            finally:
                browser.close()

    def _wait_for_login_success(self, page) -> None:
        try:
            page.wait_for_selector(
                self.LOGIN_SUCCESS_SELECTOR,
                timeout=self.CAPTCHA_WAIT_TIMEOUT_MS,
            )
        except (PlaywrightTimeoutError, TimeoutError) as exc:
            raise Exception(
                "Не удалось определить успешный вход (возможно капча не решена)"
            ) from exc

    @staticmethod
    def _extract_session_cookies(raw_cookies: list[dict[str, Any]]) -> dict[str, str]:
        collected: dict[str, str] = {}
        for cookie in raw_cookies:
            name = str(cookie.get("name", "")).strip()
            value = str(cookie.get("value", "")).strip()
            if not name or not value:
                continue
            collected[name] = value
        return collected

    @staticmethod
    def _save_cookies_to_root_config(cookies_raw: Any) -> None:
        cookies = _normalize_cookies(cookies_raw)
        if not cookies:
            return

        config_path = _resolve_config_path()
        payload: dict[str, Any] = {}
        if config_path.exists():
            try:
                loaded = Tool.load_json(config_path)
                if isinstance(loaded, dict):
                    payload = loaded
            except Exception as exc:
                Tool.write_log(
                    f"Не удалось прочитать config.json перед сохранением cookies: {exc}"
                )
                payload = {}

        normalized_payload = Tool.merge_config_with_defaults(payload)
        normalized_payload["cookies"] = cookies
        config_section = normalized_payload.get("config")
        if not isinstance(config_section, dict):
            config_section = {}
        normalized_payload["config"] = dict(config_section)
        normalized_payload["config"]["cookies"] = cookies

        Tool.save_json_atomic(config_path, normalized_payload)
        if isinstance(Config.config, dict):
            Config.config["cookies"] = cookies

    def _is_trade_search_available(self, cookies: dict[str, str]) -> bool:
        if requests is None:
            return False

        normalized_cookies = _normalize_cookies(cookies)
        if not normalized_cookies:
            return False

        payload = {
            "operationName": "tradeSearch",
            "variables": {
                "limit": 1,
                "skip": 0,
                "tradeQueryDto": {
                    "order": {
                        "expressions": [
                            {"ascending": False, "property": "REGISTERED_DATE"},
                            {"ascending": False, "property": "ID"},
                        ]
                    },
                    "sitemapPage": "purchases.trades.filters.BID_SUBMISSION",
                },
            },
            "query": (
                "query tradeSearch($tradeQueryDto: TradeQueryDtoInput, $limit: Int, $skip: Int) { "
                "trades(tradeQueryDto: $tradeQueryDto, limit: $limit, skip: $skip) { total } }"
            ),
        }
        session = requests.Session()
        try:
            session.headers.update(
                {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                    "Origin": self.BASE_URL,
                    "Referer": f"{self.BASE_URL}/",
                }
            )
            xsrf_token = str(normalized_cookies.get("XSRF-TOKEN", "") or "").strip()
            if xsrf_token:
                session.headers["X-XSRF-TOKEN"] = xsrf_token

            for key, value in normalized_cookies.items():
                key_text = str(key).strip()
                value_text = str(value).strip()
                if not key_text or not value_text:
                    continue
                session.cookies.set(key_text, value_text, domain="etp.metal-it.ru", path="/")
                session.cookies.set(key_text, value_text)

            response = session.post(
                self.TRADE_SEARCH_ENDPOINT,
                json=payload,
                timeout=max(10.0, self._timeout_ms / 1000),
            )
            return response.status_code == 200
        except Exception:
            return False
        finally:
            session.close()
