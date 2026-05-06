from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from config import Config
from tools import DatabaseTools as Tool

try:
    from playwright.sync_api import BrowserContext, Locator, Page, sync_playwright
except (ImportError, ModuleNotFoundError):  # pragma: no cover - dependency may be absent in test env
    BrowserContext = Any  # type: ignore[assignment]
    Locator = Any  # type: ignore[assignment]
    Page = Any  # type: ignore[assignment]
    sync_playwright = None  # type: ignore[assignment]


class TradeExporter:
    BASE_URL = "https://etp.metal-it.ru"
    TRADE_DETAILS_ENDPOINT_PATTERN = "{base_url}/trades/{trade_id}"
    TRADE_SEARCH_ENDPOINT = "https://etp.metal-it.ru/graphql/tradeSearch"
    TRADE_WITH_CURRENT_STAGE_ENDPOINT = "https://etp.metal-it.ru/graphql/tradeWithCurrentStage"
    GRAPHQL_FALLBACK_ENDPOINT = "https://etp.metal-it.ru/graphql"
    DEFAULT_SITEMAP_PAGE = "purchases.trades.filters.BID_SUBMISSION"
    RETRADING_SITEMAP_PAGE = "purchases.trades.filters.RETRADING"

    TRADE_SEARCH_QUERY = """
query tradeSearch($tradeQueryDto: TradeQueryDtoInput, $limit: Int, $skip: Int) {
  trades(tradeQueryDto: $tradeQueryDto, limit: $limit, skip: $skip) {
    items {
      id
      lots {
        id
      }
    }
    total
  }
}
"""

    TRADE_WITH_CURRENT_STAGE_QUERY = """
query tradeWithCurrentStage($tradeId: Int) {
  trade(id: $tradeId) {
    id
    currentStage {
      tradeResult {
        lotResults {
          bidPlaces {
            bid {
              id
              number
              price
              bidDate
              bidder {
                title
                inn
              }
              currency {
                code
              }
              status {
                title
              }
            }
          }
        }
      }
    }
  }
}
"""

    TRADE_WITH_CURRENT_STAGE_QUERY_ALT = """
query tradeWithCurrentStage($id: Int) {
  tradeWithCurrentStage(id: $id) {
    id
    currentStage {
      tradeResult {
        lotResults {
          bidPlaces {
            bid {
              id
              number
              price
              bidDate
              bidder {
                title
                inn
              }
              currency {
                code
              }
              status {
                title
              }
            }
          }
        }
      }
    }
  }
}
"""

    EXPORT_COLUMNS: tuple[str, ...] = (
        "Номер",
        "Компания",
        "ИНН",
        "Цена",
        "Валюта",
        "Статус",
        "Дата",
        "ID",
    )

    def __init__(
        self,
        *,
        headless: bool = True,
        timeout_ms: int = 30_000,
        debug_manual_export: bool = False,
        retrade_profile_dir: str = "playwright_profile",
    ) -> None:
        # headless сохранен для обратной совместимости сигнатуры.
        self._headless = bool(headless)
        self._timeout_ms = int(timeout_ms)
        self._debug_manual_export = bool(debug_manual_export)
        self._retrade_profile_dir = Path(retrade_profile_dir).expanduser()

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

    @staticmethod
    def _build_trade_search_variables(
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
            }
        )

        xsrf_token = str(cookies.get("XSRF-TOKEN", "") or "").strip()
        if xsrf_token:
            session.headers["X-XSRF-TOKEN"] = xsrf_token

        for key, value in cookies.items():
            key_text = str(key).strip()
            value_text = str(value).strip()
            if not key_text or not value_text:
                continue
            session.cookies.set(key_text, value_text)
            session.cookies.set(key_text, value_text, domain="etp.metal-it.ru", path="/")
        return session

    @classmethod
    def _build_playwright_cookies(cls, cookies: dict[str, str]) -> list[dict[str, str]]:
        payload: list[dict[str, str]] = []
        for name, value in cookies.items():
            name_text = str(name).strip()
            value_text = str(value).strip()
            if not name_text or not value_text:
                continue
            payload.append(
                {
                    "name": name_text,
                    "value": value_text,
                    "url": cls.BASE_URL,
                }
            )
        return payload

    @staticmethod
    def _write_page_debug_dump(
        page: Page,
        *,
        screenshot_path: str,
        html_path: str,
    ) -> None:
        try:
            page.screenshot(path=screenshot_path, full_page=True)
        except Exception:
            pass
        try:
            Path(html_path).write_text(page.content(), encoding="utf-8")
        except Exception:
            pass

    @staticmethod
    def _log_import(message: str) -> None:
        text = f"[IMPORT] {message}"
        print(text)
        Tool.write_log(text)

    @staticmethod
    def _click_locator_with_fallback(
        page: Page,
        locator: Locator,
        *,
        label: str,
        timeout_ms: int = 15_000,
        retries: int = 3,
    ) -> None:
        last_error: Exception | None = None
        for attempt in range(max(1, retries)):
            try:
                locator.wait_for(state="visible", timeout=timeout_ms if attempt == 0 else 5_000)
                locator.scroll_into_view_if_needed(timeout=5_000)
                locator.click(timeout=5_000)
                return
            except Exception as exc:
                last_error = exc

            try:
                element = locator.element_handle(timeout=3_000)
                if element is not None:
                    page.evaluate("(element) => element.click()", element)
                    return
            except Exception as exc:
                last_error = exc

            try:
                page.wait_for_timeout(500 * (attempt + 1))
            except Exception:
                pass

        raise RuntimeError(f"Не удалось нажать кнопку '{label}'") from last_error

    def _goto_retrade_bid_page(self, page: Page, *, bid_id: int) -> None:
        bid_id_int = self._parse_positive_int(bid_id, name="bid_id")
        retrading_url = f"{self.BASE_URL}/bids/{bid_id_int}/retrading"
        page.goto(
            retrading_url,
            wait_until="domcontentloaded",
            timeout=max(60_000, self._timeout_ms),
        )
        page.wait_for_timeout(4000)

    @staticmethod
    def _get_retrade_specification_section(page: Page) -> Locator:
        page.wait_for_selector("text=Спецификация", timeout=60_000)
        print("[EXPORT] Блок спецификации найден")

        specification_section = page.locator("section, article, div").filter(
            has_text="Спецификация"
        ).first
        if specification_section.count() == 0:
            raise RuntimeError("Не найден блок 'Спецификация'")
        return specification_section

    def _launch_retrade_persistent_context(self, playwright: Any) -> BrowserContext:
        profile_dir = self._retrade_profile_dir.resolve()
        profile_dir.mkdir(parents=True, exist_ok=True)

        try:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                headless=False,
                channel="chrome",
                args=["--disable-blink-features=AutomationControlled"],
                accept_downloads=True,
            )
            print("[EXPORT] launched persistent headed Chrome context")
            return context
        except Exception as chrome_exc:
            print("[EXPORT] chrome channel launch failed, fallback to chromium:", str(chrome_exc))
            return playwright.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
                accept_downloads=True,
            )

    def _export_retrade_bid_via_page(
        self,
        *,
        context: BrowserContext,
        bid_id: int,
        target_path: Path,
    ) -> str:
        bid_id_int = self._parse_positive_int(bid_id, name="bid_id")
        page = context.new_page()
        target_path_resolved = target_path.expanduser().resolve()

        try:
            self._goto_retrade_bid_page(page, bid_id=bid_id_int)
            specification_section = self._get_retrade_specification_section(page)

            export_button = specification_section.locator("button:has-text('Экспорт')").first
            print("[EXPORT] export_button найден:", export_button.count() > 0)
            if export_button.count() == 0:
                self._write_page_debug_dump(
                    page,
                    screenshot_path="no_export.png",
                    html_path="no_export.html",
                )
                raise RuntimeError("Кнопка 'Экспорт' не найдена в блоке 'Спецификация'")

            try:
                with page.expect_download(timeout=15_000) as download_info:
                    self._click_locator_with_fallback(
                        page,
                        export_button,
                        label="Экспорт",
                    )
            except Exception as exc:
                raise RuntimeError("Скачивание не произошло после клика по кнопке 'Экспорт'") from exc

            try:
                download = download_info.value
            except Exception as exc:
                raise RuntimeError("Не удалось получить объект скачивания после клика") from exc

            suggested_filename = str(download.suggested_filename or "").strip()
            print("[EXPORT] suggested_filename:", suggested_filename or "<empty>")

            target_path_resolved.parent.mkdir(parents=True, exist_ok=True)
            download.save_as(str(target_path_resolved))
            print("[EXPORT] сохранено в:", str(target_path_resolved))

            return str(target_path_resolved)
        except Exception:
            self._write_page_debug_dump(
                page,
                screenshot_path="export_error.png",
                html_path="export_error.html",
            )
            raise
        finally:
            try:
                page.close()
            except Exception:
                pass

    @staticmethod
    def _validate_import_file_path(file_path: str) -> Path:
        source_path = Path(file_path).expanduser().resolve()
        if source_path.suffix.lower() not in {".xlsx", ".xls"}:
            raise ValueError("Файл импорта должен иметь расширение .xlsx или .xls")
        if not source_path.exists() or not source_path.is_file():
            raise FileNotFoundError(f"Excel файл для импорта не найден: {source_path}")
        return source_path

    @staticmethod
    def _find_retrade_import_root(specification_section: Locator) -> Locator:
        import_root = specification_section.locator("um-excel-import").first
        if import_root.count() > 0:
            return import_root
        return specification_section

    def _find_retrade_import_button(
        self,
        specification_section: Locator,
    ) -> tuple[Locator, Locator]:
        import_root = self._find_retrade_import_root(specification_section)
        import_button = import_root.locator("button:has-text('Импорт')").first
        if import_button.count() == 0:
            import_button = specification_section.locator("button:has-text('Импорт')").first
        if import_button.count() == 0:
            raise RuntimeError("Кнопка 'Импорт' не найдена в блоке 'Спецификация'")
        return import_button, import_root

    @staticmethod
    def _find_retrade_import_file_input(
        page: Page,
        import_root: Locator,
        specification_section: Locator,
    ) -> Locator:
        for candidate in (
            import_root.locator("input[type='file']").first,
            specification_section.locator("um-excel-import input[type='file']").first,
            specification_section.locator("input[type='file']").first,
        ):
            if candidate.count() > 0:
                return candidate

        try:
            page.wait_for_selector("input[type='file']", timeout=15_000)
        except Exception as exc:
            raise RuntimeError("Поле выбора файла для импорта не появилось") from exc

        file_input = page.locator("input[type='file']").first
        if file_input.count() == 0:
            raise RuntimeError("Поле выбора файла для импорта не появилось")
        return file_input

    def _select_retrade_import_file(
        self,
        page: Page,
        specification_section: Locator,
        import_button: Locator,
        import_root: Locator,
        source_path: Path,
    ) -> None:
        clicked_for_chooser = False
        try:
            with page.expect_file_chooser(timeout=5_000) as chooser_info:
                self._click_locator_with_fallback(
                    page,
                    import_button,
                    label="Импорт",
                )
                clicked_for_chooser = True
            chooser_info.value.set_files(str(source_path))
            return
        except Exception:
            if not clicked_for_chooser:
                self._click_locator_with_fallback(
                    page,
                    import_button,
                    label="Импорт",
                )

        file_input = self._find_retrade_import_file_input(
            page,
            import_root,
            specification_section,
        )
        file_input.set_input_files(str(source_path))

    def _confirm_retrade_import_if_needed(self, page: Page) -> None:
        dialog = page.locator(
            "[role='dialog'], .mat-dialog-container, .cdk-overlay-pane, .modal"
        ).filter(has_text="Импорт").last
        try:
            if dialog.count() == 0:
                return
        except Exception:
            return

        for button_text in ("Подтвердить", "Загрузить", "Импорт", "ОК", "Да"):
            button = dialog.locator(f"button:has-text('{button_text}')").first
            try:
                if button.count() > 0 and button.is_visible(timeout=1_000):
                    self._click_locator_with_fallback(
                        page,
                        button,
                        label=button_text,
                        timeout_ms=5_000,
                    )
                    return
            except Exception:
                continue

    @staticmethod
    def _visible_notification_texts(page: Page) -> list[str]:
        selector = (
            "[role='alert'], .mat-snack-bar-container, simple-snack-bar, "
            ".cdk-overlay-pane, .toast, .notification, .alert"
        )
        locator = page.locator(selector)
        texts: list[str] = []
        try:
            count = min(locator.count(), 10)
        except Exception:
            return texts

        for index in range(count):
            item = locator.nth(index)
            try:
                if not item.is_visible(timeout=500):
                    continue
                text = " ".join(str(item.inner_text(timeout=1_000) or "").split())
            except Exception:
                continue
            if text:
                texts.append(text)
        return texts

    def _wait_for_retrade_import_completion(self, page: Page) -> None:
        try:
            page.wait_for_load_state("networkidle", timeout=30_000)
        except Exception:
            pass

        try:
            page.wait_for_function(
                """
() => {
  const isVisible = (element) => {
    const style = window.getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    return style.display !== 'none'
      && style.visibility !== 'hidden'
      && rect.width > 0
      && rect.height > 0;
  };
  const loaders = Array.from(document.querySelectorAll(
    'mat-progress-bar, .mat-progress-bar, mat-spinner, .mat-spinner, '
    + '.spinner, .loader, .loading, [aria-busy="true"]'
  ));
  return !loaders.some(isVisible);
}
""",
                timeout=30_000,
            )
        except Exception:
            pass

        success_pattern = re.compile(
            r"(импорт\s+выполнен|импорт.{0,80}успеш|успешно.{0,80}импорт)",
            re.IGNORECASE,
        )
        error_pattern = re.compile(
            r"(ошибка|не\s+удалось|import\s+failed|failed|error)",
            re.IGNORECASE,
        )
        for text in self._visible_notification_texts(page):
            if success_pattern.search(text):
                return
            if error_pattern.search(text):
                raise RuntimeError(f"Сайт вернул ошибку при импорте: {text}")

        try:
            body_text = page.locator("body").inner_text(timeout=5_000)
        except Exception:
            return
        if success_pattern.search(body_text):
            return

    def _import_retrade_bid_via_page(
        self,
        *,
        context: BrowserContext,
        bid_id: int,
        source_path: Path,
    ) -> str:
        bid_id_int = self._parse_positive_int(bid_id, name="bid_id")
        page = context.new_page()

        self._log_import("started")
        try:
            self._goto_retrade_bid_page(page, bid_id=bid_id_int)
            specification_section = self._get_retrade_specification_section(page)

            import_button, import_root = self._find_retrade_import_button(
                specification_section
            )
            self._log_import("import button found")

            self._select_retrade_import_file(
                page,
                specification_section,
                import_button,
                import_root,
                source_path,
            )
            self._log_import("file selected")

            self._confirm_retrade_import_if_needed(page)
            self._wait_for_retrade_import_completion(page)
            self._log_import("upload completed")
            return str(source_path)
        except Exception:
            self._write_page_debug_dump(
                page,
                screenshot_path="import_error.png",
                html_path="import_error.html",
            )
            raise
        finally:
            try:
                page.close()
            except Exception:
                pass

    def _post_graphql(
        self,
        *,
        session: requests.Session,
        endpoint: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        response = session.post(
            endpoint,
            json=payload,
            timeout=max(10.0, self._timeout_ms / 1000),
        )
        if response.status_code == 403:
            raise RuntimeError("Ошибка авторизации — обновите cookies")
        response.raise_for_status()

        body = response.json()
        if not isinstance(body, dict):
            raise RuntimeError("Некорректный формат ответа GraphQL")
        errors = body.get("errors")
        if errors:
            raise RuntimeError(f"GraphQL errors: {errors}")
        return body

    def _request_trade_page(
        self,
        *,
        session: requests.Session,
        limit: int,
        skip: int,
        sitemap_page: str,
    ) -> tuple[list[dict[str, Any]], int | None]:
        payload = {
            "operationName": "tradeSearch",
            "variables": self._build_trade_search_variables(
                limit=limit,
                skip=skip,
                sitemap_page=sitemap_page,
            ),
            "query": self.TRADE_SEARCH_QUERY,
        }
        body = self._post_graphql(
            session=session,
            endpoint=self.TRADE_SEARCH_ENDPOINT,
            payload=payload,
        )

        data = body.get("data", {})
        trades = data.get("trades", {}) if isinstance(data, dict) else {}

        items = trades.get("items", []) if isinstance(trades, dict) else []
        if not isinstance(items, list):
            items = []

        total_value: int | None = None
        if isinstance(trades, dict):
            total_raw = trades.get("total")
            try:
                parsed_total = int(total_raw)
            except (TypeError, ValueError):
                parsed_total = None
            if parsed_total is not None and parsed_total >= 0:
                total_value = parsed_total

        return items, total_value

    @staticmethod
    def _parse_positive_int(raw_value: Any, *, name: str) -> int:
        try:
            parsed = int(raw_value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Некорректный {name}: {raw_value}") from exc
        if parsed <= 0:
            raise ValueError(f"{name} должен быть положительным числом: {parsed}")
        return parsed

    @staticmethod
    def _validate_target_path(download_path: str) -> Path:
        target_path = Path(download_path).expanduser()
        if target_path.suffix.lower() not in {".xlsx", ".xls"}:
            raise ValueError("Файл экспорта должен иметь расширение .xlsx или .xls")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        return target_path

    def _load_cookies_for_export(self) -> dict[str, str]:
        cookies = self._load_cookies_from_config()
        if not cookies:
            raise ValueError("Не найдены cookies для авторизации в config.json")
        return cookies

    @staticmethod
    def _has_trade_payload(trade_payload: dict[str, Any]) -> bool:
        if not isinstance(trade_payload, dict):
            return False

        stages = trade_payload.get("submissionStages")
        if isinstance(stages, list):
            return True

        current_stage = trade_payload.get("currentStage")
        if isinstance(current_stage, dict):
            trade_result = current_stage.get("tradeResult")
            if isinstance(trade_result, dict):
                lot_results = trade_result.get("lotResults")
                if isinstance(lot_results, list):
                    return True

        return False

    @classmethod
    def _normalize_trade_payload(cls, raw_payload: Any) -> dict[str, Any]:
        if not isinstance(raw_payload, dict):
            return {}

        candidates: list[dict[str, Any]] = [raw_payload]

        data_node = raw_payload.get("data")
        if isinstance(data_node, dict):
            candidates.append(data_node)
            trade_node = data_node.get("trade")
            if isinstance(trade_node, dict):
                candidates.append(trade_node)
            trade_with_stage_node = data_node.get("tradeWithCurrentStage")
            if isinstance(trade_with_stage_node, dict):
                candidates.append(trade_with_stage_node)

        trade_node_root = raw_payload.get("trade")
        if isinstance(trade_node_root, dict):
            candidates.append(trade_node_root)

        trade_with_stage_root = raw_payload.get("tradeWithCurrentStage")
        if isinstance(trade_with_stage_root, dict):
            candidates.append(trade_with_stage_root)

        for candidate in candidates:
            if cls._has_trade_payload(candidate):
                return candidate

        return raw_payload

    def _request_trade_detail(
        self,
        *,
        session: requests.Session,
        trade_id: int,
    ) -> dict[str, Any]:
        endpoint = self.TRADE_DETAILS_ENDPOINT_PATTERN.format(
            base_url=self.BASE_URL.rstrip("/"),
            trade_id=trade_id,
        )
        response = session.get(
            endpoint,
            timeout=max(10.0, self._timeout_ms / 1000),
        )
        if response.status_code == 403:
            raise RuntimeError("Ошибка авторизации — обновите cookies")
        response.raise_for_status()

        body = response.json()
        if isinstance(body, dict):
            return body
        return {"data": body}

    def _request_trade_with_current_stage(
        self,
        *,
        session: requests.Session,
        trade_id: int,
    ) -> dict[str, Any]:
        attempts: tuple[dict[str, Any], ...] = (
            {
                "endpoint": self.TRADE_WITH_CURRENT_STAGE_ENDPOINT,
                "payload": {
                    "operationName": "tradeWithCurrentStage",
                    "variables": {"tradeId": trade_id},
                    "query": self.TRADE_WITH_CURRENT_STAGE_QUERY,
                },
            },
            {
                "endpoint": self.TRADE_WITH_CURRENT_STAGE_ENDPOINT,
                "payload": {
                    "operationName": "tradeWithCurrentStage",
                    "variables": {"id": trade_id},
                    "query": self.TRADE_WITH_CURRENT_STAGE_QUERY_ALT,
                },
            },
            {
                "endpoint": self.GRAPHQL_FALLBACK_ENDPOINT,
                "payload": {
                    "operationName": "tradeWithCurrentStage",
                    "variables": {"tradeId": trade_id},
                    "query": self.TRADE_WITH_CURRENT_STAGE_QUERY,
                },
            },
        )

        last_error: Exception | None = None
        for attempt in attempts:
            endpoint = str(attempt.get("endpoint", "") or "").strip()
            payload = attempt.get("payload")
            if not endpoint or not isinstance(payload, dict):
                continue
            try:
                return self._post_graphql(
                    session=session,
                    endpoint=endpoint,
                    payload=payload,
                )
            except Exception as exc:
                last_error = exc
                print("[EXPORT] tradeWithCurrentStage request failed:", endpoint, str(exc))

        if last_error is not None:
            raise last_error
        raise RuntimeError("Не удалось получить tradeWithCurrentStage")

    @staticmethod
    def _extract_lot_results(trade_payload: dict[str, Any]) -> list[dict[str, Any]]:
        lot_results_nodes: list[dict[str, Any]] = []

        submission_stages = trade_payload.get("submissionStages")
        if isinstance(submission_stages, list):
            for stage in submission_stages:
                if not isinstance(stage, dict):
                    continue
                trade_result = stage.get("tradeResult")
                if not isinstance(trade_result, dict):
                    continue
                lot_results = trade_result.get("lotResults")
                if not isinstance(lot_results, list):
                    continue
                for lot in lot_results:
                    if isinstance(lot, dict):
                        lot_results_nodes.append(lot)

        current_stage = trade_payload.get("currentStage")
        if isinstance(current_stage, dict):
            trade_result = current_stage.get("tradeResult")
            if isinstance(trade_result, dict):
                lot_results = trade_result.get("lotResults")
                if isinstance(lot_results, list):
                    for lot in lot_results:
                        if isinstance(lot, dict):
                            lot_results_nodes.append(lot)

        return lot_results_nodes

    def _extract_bid_rows(
        self,
        trade_payload: dict[str, Any],
        *,
        selected_bid_id: int | None = None,
        emit_logs: bool = True,
    ) -> tuple[list[dict[str, Any]], bool]:
        selected_bid_id_int: int | None = None
        if selected_bid_id is not None:
            try:
                selected_bid_id_int = int(selected_bid_id)
            except (TypeError, ValueError):
                selected_bid_id_int = None

        submission_stages = trade_payload.get("submissionStages")
        stages_count = len(submission_stages) if isinstance(submission_stages, list) else 0
        lot_results = self._extract_lot_results(trade_payload)

        if emit_logs:
            print(f"[EXPORT] submissionStages: {stages_count}")
            print(f"[EXPORT] lotResults: {len(lot_results)}")

        bids: list[dict[str, Any]] = []
        seen_keys: set[str] = set()
        has_bid_places = False

        for lot in lot_results:
            bid_places = lot.get("bidPlaces", [])
            if not isinstance(bid_places, list):
                continue

            if bid_places:
                has_bid_places = True
            if emit_logs:
                print(f"[EXPORT] bidPlaces: {len(bid_places)}")

            for place in bid_places:
                if not isinstance(place, dict):
                    continue

                bid = place.get("bid")
                if not isinstance(bid, dict):
                    continue

                bid_id_raw = bid.get("id")
                bid_id_int: int | None = None
                try:
                    bid_id_int = int(bid_id_raw)
                except (TypeError, ValueError):
                    bid_id_int = None

                if selected_bid_id_int is not None and bid_id_int != selected_bid_id_int:
                    continue

                dedupe_key = str(bid_id_int if bid_id_int is not None else bid_id_raw or "").strip()
                if dedupe_key:
                    if dedupe_key in seen_keys:
                        continue
                    seen_keys.add(dedupe_key)

                bidder = bid.get("bidder") if isinstance(bid.get("bidder"), dict) else {}
                currency = bid.get("currency") if isinstance(bid.get("currency"), dict) else {}
                status = bid.get("status") if isinstance(bid.get("status"), dict) else {}

                bids.append(
                    {
                        "Номер": bid.get("number"),
                        "Компания": bidder.get("title") if isinstance(bidder, dict) else None,
                        "ИНН": bidder.get("inn") if isinstance(bidder, dict) else None,
                        "Цена": bid.get("price"),
                        "Валюта": currency.get("code") if isinstance(currency, dict) else None,
                        "Статус": status.get("title") if isinstance(status, dict) else None,
                        "Дата": bid.get("bidDate"),
                        "ID": bid.get("id"),
                    }
                )

        if emit_logs:
            print(f"[EXPORT] найдено заявок: {len(bids)}")
            if not bids:
                print("❌ нет заявок — проверить JSON")
            if not has_bid_places:
                print("❌ bidPlaces пустой — пользователь не участвует или нет данных")

        return bids, has_bid_places

    @classmethod
    def _build_bids_dataframe(cls, bids: list[dict[str, Any]]) -> pd.DataFrame:
        if not bids:
            return pd.DataFrame(columns=list(cls.EXPORT_COLUMNS))

        frame = pd.DataFrame(bids)
        return frame.reindex(columns=list(cls.EXPORT_COLUMNS))

    @classmethod
    def _write_bids_excel(cls, *, target_path: Path, bids: list[dict[str, Any]]) -> None:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        frame = cls._build_bids_dataframe(bids)
        frame.to_excel(target_path, index=False)

    def _fetch_trade_payload_for_export(
        self,
        *,
        session: requests.Session,
        trade_id: int,
    ) -> dict[str, Any]:
        trade_detail_payload = self._request_trade_detail(session=session, trade_id=trade_id)
        trade_payload = self._normalize_trade_payload(trade_detail_payload)

        lot_results = self._extract_lot_results(trade_payload)
        if lot_results:
            return trade_payload

        print("[EXPORT] lotResults не найдены в tradeDetail, пробуем tradeWithCurrentStage")
        try:
            graphql_payload = self._request_trade_with_current_stage(
                session=session,
                trade_id=trade_id,
            )
            fallback_payload = self._normalize_trade_payload(graphql_payload)
            if self._extract_lot_results(fallback_payload):
                return fallback_payload
        except Exception as exc:
            print("[EXPORT] tradeWithCurrentStage fallback error:", str(exc))

        return trade_payload

    def _export_trade_to_excel(
        self,
        *,
        session: requests.Session,
        trade_id: int,
        target_path: Path,
        selected_bid_id: int | None = None,
    ) -> str:
        trade_payload = self._fetch_trade_payload_for_export(
            session=session,
            trade_id=trade_id,
        )
        bids, _ = self._extract_bid_rows(
            trade_payload,
            selected_bid_id=selected_bid_id,
            emit_logs=True,
        )
        self._write_bids_excel(target_path=target_path, bids=bids)
        return str(target_path.resolve())

    def _resolve_trade_id_by_lot_id(
        self,
        *,
        session: requests.Session,
        lot_id: int,
    ) -> int:
        def _match_in_sitemap(sitemap_page: str) -> int | None:
            limit = 100
            max_pages = 30
            skip = 0

            for _ in range(max_pages):
                items, total = self._request_trade_page(
                    session=session,
                    limit=limit,
                    skip=skip,
                    sitemap_page=sitemap_page,
                )
                if not items:
                    break

                for trade in items:
                    if not isinstance(trade, dict):
                        continue
                    trade_id_raw = trade.get("id")
                    try:
                        trade_id = int(trade_id_raw)
                    except (TypeError, ValueError):
                        continue

                    lots = trade.get("lots")
                    if not isinstance(lots, list):
                        continue

                    for lot in lots:
                        if not isinstance(lot, dict):
                            continue
                        try:
                            current_lot_id = int(lot.get("id"))
                        except (TypeError, ValueError):
                            continue
                        if current_lot_id == lot_id:
                            return trade_id

                if total is not None and skip + limit >= total:
                    break
                if len(items) < limit and total is None:
                    break
                skip += limit

            return None

        for sitemap_page in (self.DEFAULT_SITEMAP_PAGE, self.RETRADING_SITEMAP_PAGE):
            matched_trade_id = _match_in_sitemap(sitemap_page)
            if matched_trade_id is not None:
                print(
                    f"[EXPORT] lot_id={lot_id} найден в sitemap={sitemap_page}, trade_id={matched_trade_id}"
                )
                return matched_trade_id

        raise ValueError(f"Не удалось определить trade_id по lot_id={lot_id}")

    def _trade_contains_bid_id(
        self,
        *,
        session: requests.Session,
        trade_id: int,
        bid_id: int,
    ) -> bool:
        try:
            detail_payload = self._request_trade_detail(session=session, trade_id=trade_id)
        except Exception:
            return False

        trade_payload = self._normalize_trade_payload(detail_payload)
        bids, _ = self._extract_bid_rows(
            trade_payload,
            selected_bid_id=bid_id,
            emit_logs=False,
        )
        if bids:
            return True

        try:
            fallback_body = self._request_trade_with_current_stage(
                session=session,
                trade_id=trade_id,
            )
        except Exception:
            return False

        fallback_payload = self._normalize_trade_payload(fallback_body)
        bids, _ = self._extract_bid_rows(
            fallback_payload,
            selected_bid_id=bid_id,
            emit_logs=False,
        )
        return bool(bids)

    def _resolve_trade_id_by_bid_id(
        self,
        *,
        session: requests.Session,
        bid_id: int,
    ) -> int:
        limit = 50
        max_pages = 30
        skip = 0
        checked_trade_ids: set[int] = set()

        for _ in range(max_pages):
            items, total = self._request_trade_page(
                session=session,
                limit=limit,
                skip=skip,
                sitemap_page=self.RETRADING_SITEMAP_PAGE,
            )
            if not items:
                break

            for trade in items:
                if not isinstance(trade, dict):
                    continue
                try:
                    trade_id = int(trade.get("id"))
                except (TypeError, ValueError):
                    continue
                if trade_id <= 0 or trade_id in checked_trade_ids:
                    continue

                checked_trade_ids.add(trade_id)
                if self._trade_contains_bid_id(
                    session=session,
                    trade_id=trade_id,
                    bid_id=bid_id,
                ):
                    print(f"[EXPORT] найден trade_id={trade_id} для bid_id={bid_id}")
                    return trade_id

            if total is not None and skip + limit >= total:
                break
            if len(items) < limit and total is None:
                break
            skip += limit

        raise ValueError(f"Не удалось определить trade_id по bid_id={bid_id}")

    def export_lot_data(self, lot_id: int, download_path: str) -> str:
        lot_id_int = self._parse_positive_int(lot_id, name="lot_id")
        target_path = self._validate_target_path(download_path)
        cookies = self._load_cookies_for_export()

        session = self._build_api_session(cookies)
        try:
            trade_id = self._resolve_trade_id_by_lot_id(session=session, lot_id=lot_id_int)
            return self._export_trade_to_excel(
                session=session,
                trade_id=trade_id,
                target_path=target_path,
            )
        finally:
            session.close()

    def export_trade_data(self, trade_id: int, download_path: str) -> str:
        trade_id_int = self._parse_positive_int(trade_id, name="trade_id")
        target_path = self._validate_target_path(download_path)
        cookies = self._load_cookies_for_export()

        session = self._build_api_session(cookies)
        try:
            return self._export_trade_to_excel(
                session=session,
                trade_id=trade_id_int,
                target_path=target_path,
            )
        finally:
            session.close()

    def export_retrade_lot_data(
        self,
        lot_id: int,
        download_path: str,
        *,
        trade_id: int | None = None,
        bid_id: int | None = None,
    ) -> str:
        lot_id_int = self._parse_positive_int(lot_id, name="lot_id")
        target_path = self._validate_target_path(download_path)

        if bid_id is not None:
            selected_bid_id = self._parse_positive_int(bid_id, name="bid_id")
            return self.export_retrade_bid_data(
                bid_id=selected_bid_id,
                download_path=str(target_path),
            )

        cookies = self._load_cookies_for_export()

        session = self._build_api_session(cookies)
        try:
            if trade_id is None:
                trade_id_int = self._resolve_trade_id_by_lot_id(session=session, lot_id=lot_id_int)
            else:
                trade_id_int = self._parse_positive_int(trade_id, name="trade_id")

            return self._export_trade_to_excel(
                session=session,
                trade_id=trade_id_int,
                target_path=target_path,
            )
        finally:
            session.close()

    def export_retrade_bid_data(
        self,
        *,
        bid_id: int,
        download_path: str,
    ) -> str:
        if sync_playwright is None:
            raise RuntimeError(
                "Playwright не установлен. Установите зависимость и выполните "
                "`python -m playwright install chromium`."
            )

        bid_id_int = self._parse_positive_int(bid_id, name="bid_id")
        target_path = self._validate_target_path(download_path)
        cookies = self._load_cookies_for_export()
        playwright_cookies = self._build_playwright_cookies(cookies)
        if not playwright_cookies:
            raise RuntimeError("Не удалось подготовить cookies для Playwright")

        with sync_playwright() as playwright:
            context = self._launch_retrade_persistent_context(playwright)
            try:
                context.add_cookies(playwright_cookies)
                return self._export_retrade_bid_via_page(
                    context=context,
                    bid_id=bid_id_int,
                    target_path=target_path,
                )
            finally:
                context.close()

    def import_retrade_bid_data(
        self,
        *,
        bid_id: int,
        file_path: str,
    ) -> str:
        if sync_playwright is None:
            raise RuntimeError(
                "Playwright не установлен. Установите зависимость и выполните "
                "`python -m playwright install chromium`."
            )

        bid_id_int = self._parse_positive_int(bid_id, name="bid_id")
        source_path = self._validate_import_file_path(file_path)
        cookies = self._load_cookies_for_export()
        playwright_cookies = self._build_playwright_cookies(cookies)
        if not playwright_cookies:
            raise RuntimeError("Не удалось подготовить cookies для Playwright")

        with sync_playwright() as playwright:
            context = self._launch_retrade_persistent_context(playwright)
            try:
                context.add_cookies(playwright_cookies)
                return self._import_retrade_bid_via_page(
                    context=context,
                    bid_id=bid_id_int,
                    source_path=source_path,
                )
            finally:
                context.close()

    def import_retrade_lot_data(
        self,
        lot_id: int,
        file_path: str,
        *,
        trade_id: int | None = None,
        bid_id: int | None = None,
    ) -> str:
        self._parse_positive_int(lot_id, name="lot_id")
        if trade_id is not None:
            self._parse_positive_int(trade_id, name="trade_id")
        if bid_id is None:
            raise RuntimeError("Выберите предложение переторжки")
        selected_bid_id = self._parse_positive_int(bid_id, name="bid_id")
        return self.import_retrade_bid_data(
            bid_id=selected_bid_id,
            file_path=file_path,
        )

    def export_trade(self, trade_id: int, download_path: str) -> str:
        return self.export_trade_data(trade_id=trade_id, download_path=download_path)

    def export_lot(self, lot_id: int, download_path: str) -> str:
        return self.export_lot_data(lot_id=lot_id, download_path=download_path)

    def export_retrade_lot(self, lot_id: int, download_path: str) -> str:
        return self.export_retrade_lot_data(lot_id=lot_id, download_path=download_path)

    def import_retrade_lot(self, lot_id: int, file_path: str, *, bid_id: int | None = None) -> str:
        return self.import_retrade_lot_data(lot_id=lot_id, file_path=file_path, bid_id=bid_id)

    def export_retrade(
        self,
        lot_id: int,
        download_path: str,
        *,
        trade_id: int | None = None,
        bid_id: int | None = None,
    ) -> str:
        return self.export_retrade_lot_data(
            lot_id=lot_id,
            download_path=download_path,
            trade_id=trade_id,
            bid_id=bid_id,
        )

    def import_retrade(
        self,
        lot_id: int,
        file_path: str,
        *,
        trade_id: int | None = None,
        bid_id: int | None = None,
    ) -> str:
        return self.import_retrade_lot_data(
            lot_id=lot_id,
            file_path=file_path,
            trade_id=trade_id,
            bid_id=bid_id,
        )
