from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import requests

from config import Config
from tools import DatabaseTools as Tool

try:
    from playwright.sync_api import BrowserContext, Page, sync_playwright
except ModuleNotFoundError:  # pragma: no cover - dependency may be absent in test env
    BrowserContext = Any  # type: ignore[assignment]
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

    def __init__(self, *, headless: bool = True, timeout_ms: int = 30_000) -> None:
        # headless сохранен для обратной совместимости сигнатуры.
        self._headless = bool(headless)
        self._timeout_ms = int(timeout_ms)

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

    def _export_retrade_bid_via_page(
        self,
        *,
        context: BrowserContext,
        bid_id: int,
        target_path: Path,
    ) -> str:
        bid_id_int = self._parse_positive_int(bid_id, name="bid_id")
        retrading_url = f"{self.BASE_URL}/bids/{bid_id_int}/retrading"
        page = context.new_page()
        target_path_resolved = target_path.expanduser().resolve()
        export_saved_via_response = False
        export_saved_via_blob = False
        export_response_urls: list[str] = []

        def handle_request(request: Any) -> None:
            print("REQ:", str(getattr(request, "url", "") or ""))

        def handle_console(message: Any) -> None:
            try:
                print("BROWSER:", str(getattr(message, "text", "") or ""))
            except Exception:
                pass

        def handle_response(response: Any) -> None:
            nonlocal export_saved_via_response

            url = str(getattr(response, "url", "") or "")
            lower_url = url.lower()
            if not any(token in lower_url for token in ("export", "excel", "xlsx", "download", "report")):
                return

            export_response_urls.append(url)
            print("🔥 EXPORT RESPONSE:", url)

            try:
                response_body = response.body()
                if not isinstance(response_body, (bytes, bytearray)) or len(response_body) == 0:
                    raise RuntimeError("Пустое тело ответа")
                target_path_resolved.parent.mkdir(parents=True, exist_ok=True)
                with target_path_resolved.open("wb") as file:
                    file.write(bytes(response_body))
                export_saved_via_response = True
                print("✅ Файл сохранён через response")
            except Exception as exc:
                print("❌ Ошибка сохранения:", str(exc))

        page.on("request", handle_request)
        page.on("console", handle_console)
        page.on("response", handle_response)

        try:
            page.goto(
                retrading_url,
                wait_until="domcontentloaded",
                timeout=max(60_000, self._timeout_ms),
            )
            page.wait_for_timeout(3000)
            page.wait_for_timeout(5000)

            page.wait_for_selector("text=Спецификация", timeout=60_000)
            print("[EXPORT] Блок спецификации найден")

            for _ in range(10):
                page.mouse.wheel(0, 3000)
                page.wait_for_timeout(500)

            specification_block = page.locator("section, article, div").filter(
                has_text="Спецификация"
            )
            export_button = specification_block.first.locator("button:has-text('Экспорт')").first
            if export_button.count() == 0:
                export_button = page.locator("button:has-text('Экспорт')").first

            if export_button.count() == 0:
                print("❌ Кнопка не найдена — сохраняю debug")
                self._write_page_debug_dump(
                    page,
                    screenshot_path="no_export.png",
                    html_path="no_export.html",
                )
                raise RuntimeError("Кнопка Экспорт не найдена")

            print("[EXPORT] Кнопка найдена")
            page.evaluate(
                """
                () => {
                    if (!window.__codexClickLoggerInstalled) {
                        window.__codexClickLoggerInstalled = true;
                        document.addEventListener(
                            "click",
                            (event) => {
                                const target = event.target && event.target.closest
                                    ? event.target.closest("button,[role='button'],a,span,div")
                                    : event.target;
                                const text = target
                                    ? String(target.innerText || target.textContent || "").trim().slice(0, 160)
                                    : "";
                                const tag = target && target.tagName
                                    ? target.tagName.toLowerCase()
                                    : "unknown";
                                console.log(`🖱 CLICK ${tag}: ${text}`);
                            },
                            true
                        );
                    }

                    window.__lastBlob = null;
                    window.__fileName = null;

                    const urlObject = window.URL || URL;
                    if (!urlObject.__codexOriginalCreateObjectURL) {
                        urlObject.__codexOriginalCreateObjectURL =
                            urlObject.createObjectURL.bind(urlObject);
                    }

                    urlObject.createObjectURL = function(blob) {
                        window.__lastBlob = blob || null;
                        console.log("🔥 BLOB CAPTURED", blob);
                        return urlObject.__codexOriginalCreateObjectURL(blob);
                    };

                    const originalSaveAs =
                        typeof window.saveAs === "function" ? window.saveAs : null;

                    window.saveAs = function(blob, name) {
                        window.__lastBlob = blob || null;
                        window.__fileName = name || null;
                        console.log("🔥 saveAs intercepted");
                        if (originalSaveAs) {
                            return originalSaveAs.apply(this, arguments);
                        }
                        return undefined;
                    };
                }
                """
            )

            def _save_blob_to_disk() -> bool:
                nonlocal export_saved_via_blob
                blob_data = page.evaluate(
                    """
                    async () => {
                        if (!window.__lastBlob) return null;
                        const arrayBuffer = await window.__lastBlob.arrayBuffer();
                        return Array.from(new Uint8Array(arrayBuffer));
                    }
                    """
                )
                if isinstance(blob_data, list) and len(blob_data) > 0:
                    target_path_resolved.parent.mkdir(parents=True, exist_ok=True)
                    with target_path_resolved.open("wb") as file:
                        file.write(bytes(blob_data))
                    export_saved_via_blob = True
                    print("✅ Excel сохранён через Blob")
                    return True
                return False

            def _wait_for_export_signal(wait_ms: int = 3000) -> bool:
                page.wait_for_timeout(wait_ms)
                if _save_blob_to_disk():
                    return True
                return bool(export_saved_via_response)

            def _realistic_click(locator: Any, label: str) -> bool:
                try:
                    locator.scroll_into_view_if_needed()
                    page.wait_for_timeout(250)
                    try:
                        locator.hover(timeout=3000)
                    except Exception as hover_exc:
                        print("[EXPORT] hover skipped:", label, str(hover_exc))
                    page.wait_for_timeout(300)
                    locator.click(timeout=5000)
                    print("[EXPORT] clicked:", label)
                    return True
                except Exception as click_exc:
                    print("[EXPORT] click failed:", label, str(click_exc))
                    return False

            def _try_locator_group(group_label: str, locator: Any) -> bool:
                try:
                    count = locator.count()
                except Exception:
                    count = 0
                if count <= 0:
                    return False

                for index in range(min(count, 3)):
                    candidate = locator.nth(index)
                    if _realistic_click(candidate, f"{group_label}#{index}"):
                        if _wait_for_export_signal(3000):
                            return True

                    child_locator = candidate.locator(
                        "[onclick], [ng-click], [data-bind*='click'], [role='button'], button, a, span, div"
                    )
                    try:
                        child_count = child_locator.count()
                    except Exception:
                        child_count = 0
                    for child_index in range(min(child_count, 3)):
                        child = child_locator.nth(child_index)
                        if _realistic_click(child, f"{group_label}#{index}/child#{child_index}"):
                            if _wait_for_export_signal(3000):
                                return True

                return False

            export_candidates: list[tuple[str, Any]] = [
                ("spec role button", specification_block.first.get_by_role("button", name="Экспорт")),
                ("spec button", specification_block.first.locator("button:has-text('Экспорт')")),
                ("spec role='button'", specification_block.first.locator("[role='button']:has-text('Экспорт')")),
                ("spec span", specification_block.first.locator("span:has-text('Экспорт')")),
                ("spec div", specification_block.first.locator("div:has-text('Экспорт')")),
                ("page role button", page.get_by_role("button", name="Экспорт")),
                ("page button", page.locator("button:has-text('Экспорт')")),
                ("page role='button'", page.locator("[role='button']:has-text('Экспорт')")),
                ("page span", page.locator("span:has-text('Экспорт')")),
                ("page div", page.locator("div:has-text('Экспорт')")),
                ("page any text", page.locator("text=Экспорт")),
            ]

            export_started = False
            for group_label, candidate_locator in export_candidates:
                if _try_locator_group(group_label, candidate_locator):
                    export_started = True
                    break

            if not export_started:
                js_clicked = page.evaluate(
                    """
                    () => {
                        const normalize = (value) => String(value || "").trim().toLowerCase();
                        const hasExportText = (node) =>
                            normalize(node.innerText || node.textContent).includes("экспорт");

                        const selectors = [
                            "button",
                            "[role='button']",
                            "a",
                            "span",
                            "div",
                            "[ng-click]",
                            "[onclick]",
                            "[data-bind*='click']",
                        ];

                        const all = Array.from(document.querySelectorAll(selectors.join(",")));
                        const target = all.find((node) => hasExportText(node));
                        if (!target) return false;

                        const child = target.querySelector(
                            "[onclick], [ng-click], [data-bind*='click'], button, [role='button'], a, span, div"
                        );
                        const clickable = child || target;

                        clickable.scrollIntoView({ block: "center", inline: "center" });
                        clickable.dispatchEvent(new MouseEvent("mouseover", { bubbles: true }));
                        clickable.dispatchEvent(new MouseEvent("mousemove", { bubbles: true }));
                        clickable.dispatchEvent(new MouseEvent("mousedown", { bubbles: true }));
                        clickable.dispatchEvent(new MouseEvent("mouseup", { bubbles: true }));
                        clickable.click();
                        console.log("🔥 JS EXPORT CLICK", String(clickable.innerText || clickable.textContent || "").trim());
                        return true;
                    }
                    """
                )
                print("[EXPORT] JS fallback clicked:", bool(js_clicked))
                if js_clicked and _wait_for_export_signal(4000):
                    export_started = True

            if not export_started:
                internal_fn = page.evaluate(
                    """
                    () => {
                        const keys = Object.keys(window).filter((key) =>
                            /export|excel|download/i.test(key)
                        );
                        for (const key of keys.slice(0, 30)) {
                            const candidate = window[key];
                            if (typeof candidate !== "function" || candidate.length > 0) continue;
                            try {
                                candidate();
                                console.log("🔥 WINDOW FUNCTION CALLED", key);
                                return key;
                            } catch (_error) {
                                // keep probing safe no-arg functions
                            }
                        }
                        return null;
                    }
                    """
                )
                if internal_fn:
                    print("[EXPORT] internal function called:", str(internal_fn))
                    if _wait_for_export_signal(4000):
                        export_started = True

            if export_saved_via_blob or export_saved_via_response or export_started:
                return str(target_path_resolved)

            Path("after_click.html").write_text(page.content(), encoding="utf-8")
            print("⚠️ EXPORT не пойман — смотри HTML")
            if export_response_urls:
                print("[EXPORT] candidate URLs:", export_response_urls)
            raise RuntimeError("Не удалось запустить экспорт после реалистичных кликов и JS fallback")
        except Exception:
            self._write_page_debug_dump(
                page,
                screenshot_path="export_error.png",
                html_path="export_error.html",
            )
            raise
        finally:
            try:
                page.remove_listener("request", handle_request)
            except Exception:
                pass
            try:
                page.remove_listener("console", handle_console)
            except Exception:
                pass
            try:
                page.remove_listener("response", handle_response)
            except Exception:
                pass
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
            browser = playwright.chromium.launch(headless=self._headless)
            try:
                context = browser.new_context(accept_downloads=True)
                context.add_cookies(playwright_cookies)
                return self._export_retrade_bid_via_page(
                    context=context,
                    bid_id=bid_id_int,
                    target_path=target_path,
                )
            finally:
                browser.close()

    def export_trade(self, trade_id: int, download_path: str) -> str:
        return self.export_trade_data(trade_id=trade_id, download_path=download_path)

    def export_lot(self, lot_id: int, download_path: str) -> str:
        return self.export_lot_data(lot_id=lot_id, download_path=download_path)

    def export_retrade_lot(self, lot_id: int, download_path: str) -> str:
        return self.export_retrade_lot_data(lot_id=lot_id, download_path=download_path)

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
