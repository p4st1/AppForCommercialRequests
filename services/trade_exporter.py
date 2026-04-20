from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

from config import Config
from tools import DatabaseTools as Tool


def open_retrading(page: Page, trade_id: int, stage_id: int) -> str:
    trade_id_int = int(trade_id)
    stage_id_int = int(stage_id)
    url = (
        "https://etp.metal-it.ru/trades/"
        f"{trade_id_int}/submission-stages/{stage_id_int}"
        "?page=purchases.trades.filters.RETRADING"
    )
    print(f"[RETRADE] open trade_id={trade_id_int}, stage_id={stage_id_int}")
    print(f"[RETRADE] open url={url}")

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    except Exception as exc:
        print("Не удалось открыть страницу переторжки")
        raise Exception("Не удалось открыть страницу переторжки") from exc

    try:
        page.wait_for_load_state("networkidle", timeout=60_000)
    except Exception:
        pass

    try:
        page.wait_for_selector("table", timeout=60_000)
    except Exception:
        page.wait_for_timeout(3_000)

    if str(trade_id_int) not in str(page.url):
        print("[WARNING] URL не содержит trade_id")

    header_locator = page.locator("h1")
    if header_locator.count() == 0:
        print("[ERROR] Заголовок переторжки не найден")
        raise Exception("Страница переторжки не загрузилась корректно")

    title_text = str(header_locator.first.inner_text() or "").strip()
    print(f"[DEBUG] Открыта страница: {title_text}")

    page.evaluate(
        """
        document.body.style.border = "5px solid red";
        """
    )

    filename = f"debug_retrading_{trade_id_int}.png"
    page.screenshot(path=filename, full_page=True)
    print(f"[DEBUG] Скриншот сохранён: {filename}")

    return url


def open_bid(page: Page, bid_id: int) -> str:
    bid_id_int = int(bid_id)
    url = f"https://etp.metal-it.ru/bids/{bid_id_int}/retrading"
    print("[DEBUG] open bid url:", url)
    page.goto(url, timeout=60_000)
    page.wait_for_load_state("networkidle", timeout=60_000)
    return url


def _save_export_debug(page: Page) -> None:
    page.screenshot(path="export_debug.png")
    Path("export_debug.html").write_text(page.content(), encoding="utf-8")


def _is_export_like_url(url: str) -> bool:
    lower_url = str(url or "").lower()
    return any(token in lower_url for token in ("/export", "/report", "/file", ".xlsx", "xlsx"))


def _pick_export_url(
    request_urls: list[str],
    response_records: list[dict[str, Any]],
) -> str | None:
    for record in reversed(response_records):
        url = str(record.get("url", "") or "")
        status = int(record.get("status", 0) or 0)
        headers = record.get("headers", {})
        content_type = str(headers.get("content-type", "")).lower() if isinstance(headers, dict) else ""
        content_disposition = (
            str(headers.get("content-disposition", "")).lower() if isinstance(headers, dict) else ""
        )
        if status >= 400:
            continue
        if (
            "attachment" in content_disposition
            or "spreadsheet" in content_type
            or "excel" in content_type
            or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in content_type
            or _is_export_like_url(url)
        ):
            return url

    for url in reversed(request_urls):
        if _is_export_like_url(url):
            return url
    return None


def _filename_from_response_headers(headers: dict[str, Any], bid_id: int) -> str:
    content_disposition = str(headers.get("content-disposition", "") or "")
    matches = re.findall(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', content_disposition, flags=re.IGNORECASE)
    if matches:
        name = str(matches[-1]).strip()
        if name:
            return name
    return f"retrade_{bid_id}.xlsx"


def _download_export_from_captured_url(
    page: Page,
    *,
    file_url: str,
    download_dir: str,
    bid_id: int,
) -> str:
    absolute_url = urljoin(page.url, file_url)
    session = requests.Session()
    try:
        for cookie in page.context.cookies():
            name = str(cookie.get("name", "") or "").strip()
            value = str(cookie.get("value", "") or "").strip()
            if not name or not value:
                continue
            domain = str(cookie.get("domain", "") or "").strip() or "etp.metal-it.ru"
            path = str(cookie.get("path", "") or "").strip() or "/"
            session.cookies.set(name, value, domain=domain, path=path)

        session.headers.update(
            {
                "Accept": "*/*",
                "Referer": page.url,
                "Origin": "https://etp.metal-it.ru",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            }
        )

        response = session.get(
            absolute_url,
            timeout=60,
            stream=True,
            allow_redirects=True,
        )
        response.raise_for_status()

        filename = _filename_from_response_headers(dict(response.headers), bid_id)
        parsed_url_path = Path(urlparse(str(response.url)).path)
        if filename == f"retrade_{bid_id}.xlsx" and parsed_url_path.name:
            filename = parsed_url_path.name

        if not filename.lower().endswith((".xlsx", ".xls")):
            filename = f"{filename}.xlsx"

        save_dir = Path(download_dir).expanduser()
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = (save_dir / filename).resolve()

        with save_path.open("wb") as output_file:
            for chunk in response.iter_content(chunk_size=65_536):
                if chunk:
                    output_file.write(chunk)

        if not save_path.exists() or save_path.stat().st_size <= 0:
            raise RuntimeError("Файл не скачан или пустой")

        print("[DEBUG] файл:", filename)
        print("[SUCCESS] файл скачан:", str(save_path))
        return str(save_path)
    finally:
        session.close()


def export_retrading_table(page: Page, bid_id: int, download_dir: str) -> str:
    bid_id_int = int(bid_id)
    if bid_id_int <= 0:
        raise ValueError(f"Некорректный bid_id: {bid_id_int}")

    download_path = Path(download_dir).expanduser()
    download_path.mkdir(parents=True, exist_ok=True)

    url = f"https://etp.metal-it.ru/bids/{bid_id_int}/retrading"
    print("[DEBUG] open:", url)

    request_urls: list[str] = []
    response_records: list[dict[str, Any]] = []

    def _on_request(request: Any) -> None:
        request_url = str(getattr(request, "url", "") or "")
        request_urls.append(request_url)
        print("[REQUEST]", request_url)

    def _on_response(response: Any) -> None:
        response_url = str(getattr(response, "url", "") or "")
        print("[RESPONSE]", response_url)
        headers: dict[str, Any] = {}
        try:
            headers = dict(response.headers)
        except Exception:
            headers = {}
        response_records.append(
            {
                "url": response_url,
                "status": int(getattr(response, "status", 0) or 0),
                "headers": headers,
            }
        )

    page.on("request", _on_request)
    page.on("response", _on_response)
    try:
        page.goto(url, timeout=60_000)
        page.wait_for_load_state("networkidle", timeout=60_000)
        print("[DEBUG] page url:", page.url)
        _save_export_debug(page)
        try:
            page.wait_for_selector("text=Экспорт", timeout=60_000)
        except Exception as exc:
            print("[ERROR] кнопка Экспорт не найдена")
            Path("debug_export.html").write_text(page.content(), encoding="utf-8")
            raise RuntimeError("Кнопка Экспорт не найдена") from exc

        print("[DEBUG] ищем кнопку Экспорт")
        button = page.get_by_text("Экспорт", exact=False).first
        print("[DEBUG] button found:", button)
        if button.count() == 0:
            raise RuntimeError("Не удалось найти кнопку Экспорт")

        element_handle = button.element_handle(timeout=10_000)
        if element_handle is None:
            raise RuntimeError("Не удалось получить элемент кнопки Экспорт")

        print("[DEBUG] нажимаем Экспорт")
        page.evaluate("(el) => el.click()", element_handle)
        page.wait_for_timeout(5000)

        captured_export_url = _pick_export_url(request_urls, response_records)
        if captured_export_url:
            print("[DEBUG] captured export url:", captured_export_url)
            return _download_export_from_captured_url(
                page,
                file_url=captured_export_url,
                download_dir=str(download_path),
                bid_id=bid_id_int,
            )

        with page.expect_download(timeout=15_000) as download_info:
            element_handle_retry = button.element_handle(timeout=10_000)
            if element_handle_retry is None:
                raise RuntimeError("Не удалось получить элемент кнопки Экспорт для повторного клика")
            page.evaluate("(el) => el.click()", element_handle_retry)

        download = download_info.value
        filename = str(download.suggested_filename or f"retrade_{bid_id_int}.xlsx")
        print("[DEBUG] файл:", filename)

        path = os.path.join(str(download_path), filename)
        download.save_as(path)
        print("[SUCCESS] файл скачан:", path)
        return str(Path(path).resolve())
    except PlaywrightTimeoutError:
        _save_export_debug(page)
        page.screenshot(path="export_error.png")
        Path("export_error.html").write_text(page.content(), encoding="utf-8")
        raise Exception("Экспорт не сработал — см. export_debug.html и логи REQUEST")
    except Exception:
        _save_export_debug(page)
        page.screenshot(path="export_error.png")
        Path("export_error.html").write_text(page.content(), encoding="utf-8")
        raise Exception("Экспорт не сработал — см. export_debug.html и логи REQUEST")
    finally:
        try:
            page.remove_listener("request", _on_request)
        except Exception:
            pass
        try:
            page.remove_listener("response", _on_response)
        except Exception:
            pass


def _unwrap_trade_json(raw_payload: Any) -> dict[str, Any]:
    if isinstance(raw_payload, dict) and isinstance(raw_payload.get("data"), dict):
        return raw_payload["data"]
    if isinstance(raw_payload, dict):
        return raw_payload
    return {}


def _parse_bids_from_trade_data(data: dict[str, Any]) -> list[dict[str, Any]]:
    submission_stages = data.get("submissionStages", [])
    if not isinstance(submission_stages, list):
        submission_stages = []
    print("submissionStages:", len(submission_stages))

    bids: list[dict[str, Any]] = []
    seen_bid_ids: set[int] = set()

    for stage in submission_stages:
        if not isinstance(stage, dict):
            continue
        trade_result = stage.get("tradeResult")
        if not isinstance(trade_result, dict):
            continue

        lot_results = trade_result.get("lotResults")
        if not isinstance(lot_results, list):
            lot_results = []
        print("lotResults:", len(lot_results))

        for lot in lot_results:
            if not isinstance(lot, dict):
                continue
            bid_places = lot.get("bidPlaces")
            if not isinstance(bid_places, list):
                bid_places = []
            print("bidPlaces:", len(bid_places))

            for place in bid_places:
                if not isinstance(place, dict):
                    continue
                bid = place.get("bid")
                if not isinstance(bid, dict):
                    continue

                bid_id_raw = bid.get("id")
                try:
                    bid_id = int(bid_id_raw)
                except (TypeError, ValueError):
                    continue
                if bid_id <= 0 or bid_id in seen_bid_ids:
                    continue

                status_title = ""
                status_node = bid.get("status")
                if isinstance(status_node, dict):
                    status_title = str(status_node.get("title", "") or "")
                elif status_node is not None:
                    status_title = str(status_node)

                bids.append(
                    {
                        "bid_id": bid_id,
                        "number": str(bid.get("number", "") or ""),
                        "price": bid.get("price"),
                        "status": status_title,
                    }
                )
                seen_bid_ids.add(bid_id)

    return bids


def get_trade_json_via_network(page: Page, trade_id: int) -> dict[str, Any]:
    trade_id_int = int(trade_id)
    target_url = f"https://etp.metal-it.ru/trades/{trade_id_int}"

    captured_payload: Any = None
    captured_url = ""
    fallback_payload: Any = None
    fallback_url = ""

    def _on_response(response: Any) -> None:
        nonlocal captured_payload, captured_url, fallback_payload, fallback_url

        response_url = str(getattr(response, "url", "") or "")
        lower_url = response_url.lower()
        if "trade" not in lower_url and "bid" not in lower_url:
            return

        try:
            response_json: Any = response.json()
        except Exception:
            return

        try:
            payload_text = json.dumps(response_json, ensure_ascii=False, default=str)
        except Exception:
            payload_text = str(response_json)

        if f"/trades/{trade_id_int}" in response_url:
            fallback_payload = response_json
            fallback_url = response_url

        if "bidPlaces" in payload_text or '"number"' in payload_text:
            captured_payload = response_json
            captured_url = response_url

    page.on("response", _on_response)
    try:
        page.goto(target_url, wait_until="domcontentloaded", timeout=60_000)
        for _ in range(14):
            if captured_payload is not None:
                break
            page.wait_for_timeout(500)
    finally:
        try:
            page.remove_listener("response", _on_response)
        except Exception:
            pass

    if captured_payload is not None:
        try:
            payload_text = json.dumps(captured_payload, ensure_ascii=False, default=str)
        except Exception:
            payload_text = str(captured_payload)
        print("FOUND TARGET API:", captured_url)
        print(payload_text[:1000])
        if isinstance(captured_payload, dict):
            return captured_payload
        return {"data": captured_payload}

    if fallback_payload is not None:
        try:
            payload_text = json.dumps(fallback_payload, ensure_ascii=False, default=str)
        except Exception:
            payload_text = str(fallback_payload)
        print("FOUND TARGET API:", fallback_url)
        print(payload_text[:1000])
        if isinstance(fallback_payload, dict):
            return fallback_payload
        return {"data": fallback_payload}

    raise RuntimeError(
        f"Не удалось автоматически найти API с заявками для trade_id={trade_id_int}"
    )


def get_trade_bids(page: Page, trade_id: int) -> list[dict[str, Any]]:
    trade_id_int = int(trade_id)
    endpoint = f"https://etp.metal-it.ru/trades/{trade_id_int}"
    response = page.request.get(endpoint, timeout=60_000)

    print(response.status)
    response_text = response.text()
    print(response_text[:1000])

    if not response.ok:
        raise RuntimeError(
            f"Не удалось получить заявки переторжки trade_id={trade_id_int}: HTTP {response.status}"
        )

    raw_data: Any = {}
    try:
        raw_data = response.json()
    except Exception as exc:
        raise RuntimeError(
            f"Некорректный JSON ответа /trades/{trade_id_int}: {response_text[:1000]}"
        ) from exc

    data = _unwrap_trade_json(raw_data)
    print("data.keys():", list(data.keys()))

    submission_stages = data.get("submissionStages")
    if not isinstance(submission_stages, list):
        print("submissionStages отсутствует — проблема авторизации")
        raw_data = get_trade_json_via_network(page, trade_id_int)
        data = _unwrap_trade_json(raw_data)

    bids = _parse_bids_from_trade_data(data)

    if not bids:
        raw_data = get_trade_json_via_network(page, trade_id_int)
        data = _unwrap_trade_json(raw_data)
        bids = _parse_bids_from_trade_data(data)

    if not bids:
        raw_text = response_text
        try:
            raw_text = json.dumps(raw_data, ensure_ascii=False, default=str)
        except Exception:
            pass
        print("response.text[:1000]:", raw_text[:1000])
        print("data.keys():", list(data.keys()))

    print(f"[DEBUG] найдено заявок: {len(bids)}")
    return bids


class TradeExporter:
    BASE_URL = "https://etp.metal-it.ru"
    TRADE_SEARCH_ENDPOINT = "https://etp.metal-it.ru/graphql/tradeSearch"
    TRADE_WITH_CURRENT_STAGE_ENDPOINT = "https://etp.metal-it.ru/graphql/tradeWithCurrentStage"
    GRAPHQL_FALLBACK_ENDPOINT = "https://etp.metal-it.ru/graphql"
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
  }
}
"""
    RETRADE_STAGE_SEARCH_QUERY = """
query tradeSearch($tradeQueryDto: TradeQueryDtoInput, $limit: Int, $skip: Int) {
  trades(tradeQueryDto: $tradeQueryDto, limit: $limit, skip: $skip) {
    items {
      id
      currentStage {
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
    currentStage {
      tradeResult {
        lotResults {
          bidPlaces {
            bid {
              id
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
    currentStage {
      tradeResult {
        lotResults {
          bidPlaces {
            bid {
              id
            }
          }
        }
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
    def _build_trade_search_variables(
        limit: int,
        skip: int,
        *,
        sitemap_page: str = "purchases.trades.filters.BID_SUBMISSION",
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
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict):
            raise RuntimeError("Некорректный формат ответа GraphQL")
        errors = body.get("errors")
        if errors:
            raise RuntimeError(f"GraphQL errors: {errors}")
        return body

    def _resolve_retrade_stage_id(
        self,
        *,
        session: requests.Session,
        trade_id: int,
    ) -> int:
        print(f"[PIPELINE] STEP 1: tradeSearch retrades for trade_id={trade_id}")
        limit = 100
        max_pages = 30
        skip = 0
        total = 0

        for _ in range(max_pages):
            payload = {
                "operationName": "tradeSearch",
                "variables": self._build_trade_search_variables(
                    limit=limit,
                    skip=skip,
                    sitemap_page=self.RETRADING_SITEMAP_PAGE,
                ),
                "query": self.RETRADE_STAGE_SEARCH_QUERY,
            }
            body = self._post_graphql(
                session=session,
                endpoint=self.TRADE_SEARCH_ENDPOINT,
                payload=payload,
            )
            data = body.get("data", {})
            trades = data.get("trades", {}) if isinstance(data, dict) else {}
            items = trades.get("items", []) if isinstance(trades, dict) else []
            total_raw = trades.get("total", total) if isinstance(trades, dict) else total
            try:
                total = max(0, int(total_raw))
            except (TypeError, ValueError):
                total = 0

            if not isinstance(items, list) or not items:
                break

            for trade in items:
                if not isinstance(trade, dict):
                    continue
                trade_raw = trade.get("id")
                try:
                    current_trade_id = int(trade_raw)
                except (TypeError, ValueError):
                    continue
                if current_trade_id != trade_id:
                    continue

                current_stage = trade.get("currentStage")
                if not isinstance(current_stage, dict):
                    raise RuntimeError(
                        f"Не найден currentStage для trade_id={trade_id}"
                    )
                stage_id = self._parse_positive_int(
                    current_stage.get("id"),
                    name="stage_id",
                )
                print(f"[PIPELINE] STEP 1 DONE: trade_id={trade_id}, stage_id={stage_id}")
                return stage_id

            if total > 0 and skip + limit >= total:
                break
            if len(items) < limit and total <= 0:
                break
            skip += limit

        raise RuntimeError(f"Не найдена переторжка trade_id={trade_id} в tradeSearch")

    @staticmethod
    def _extract_bid_id_from_trade_with_current_stage_data(
        response_body: dict[str, Any],
        *,
        current_user_id: int | None = None,
        trade_id: int | None = None,
    ) -> int | None:
        if not isinstance(response_body, dict):
            print("Ошибка: некорректный формат response tradeWithCurrentStage")
            return None

        print(json.dumps(response_body, indent=2, ensure_ascii=False, default=str))

        data_node = response_body.get("data")
        if not isinstance(data_node, dict):
            print("Ошибка: в response отсутствует data")
            return None

        trade_node = data_node.get("trade")
        if not isinstance(trade_node, dict):
            print("Ошибка: отсутствует data['trade'], пробуем data['tradeWithCurrentStage']")
            trade_node = data_node.get("tradeWithCurrentStage")
        if not isinstance(trade_node, dict):
            print("Ошибка: не найден data['trade'] или data['tradeWithCurrentStage']")
            return None

        current_stage = trade_node.get("currentStage")
        if not isinstance(current_stage, dict):
            print("Ошибка: отсутствует data['trade']['currentStage']")
            return None

        trade_result = current_stage.get("tradeResult")
        if not isinstance(trade_result, dict):
            print("Ошибка: отсутствует data['trade']['currentStage']['tradeResult']")
            return None

        lot_results = trade_result.get("lotResults")
        print("lotResults:", lot_results)
        if not isinstance(lot_results, list) or not lot_results:
            print("Нет bidPlaces — либо пользователь не участвует, либо API вернул пусто")
            return None

        has_bid = False
        for lot in lot_results:
            if isinstance(lot, dict) and lot.get("bidPlaces"):
                has_bid = True
                break
        if not has_bid:
            if trade_id is not None:
                print(f"Пропуск: нет участия в переторжке {trade_id}")
            print("Нет bidPlaces — либо пользователь не участвует, либо API вернул пусто")
            return None

        first_available_bid_id: int | None = None

        for lot in lot_results:
            print("lot:", lot)
            if not isinstance(lot, dict):
                print("bidPlaces:", None)
                continue
            bid_places = lot.get("bidPlaces")
            print("bidPlaces:", bid_places)
            if not isinstance(bid_places, list) or not bid_places:
                continue

            for place in bid_places:
                if not isinstance(place, dict):
                    continue
                if "bid" not in place or place.get("bid") is None:
                    continue

                bid_node = place.get("bid")
                if not isinstance(bid_node, dict):
                    continue

                bid_id_raw = bid_node.get("id")
                try:
                    bid_id = int(bid_id_raw)
                except (TypeError, ValueError):
                    continue
                if bid_id <= 0:
                    continue

                if first_available_bid_id is None:
                    first_available_bid_id = bid_id

                if current_user_id is not None:
                    bidder_node = bid_node.get("bidder")
                    bidder_id_raw = bidder_node.get("id") if isinstance(bidder_node, dict) else None
                    try:
                        bidder_id = int(bidder_id_raw) if bidder_id_raw is not None else None
                    except (TypeError, ValueError):
                        bidder_id = None
                    if bidder_id == current_user_id:
                        print("Найден bid_id:", bid_id)
                        return bid_id

        if first_available_bid_id is not None:
            print("Найден bid_id:", first_available_bid_id)
            return first_available_bid_id

        print("Нет bidPlaces — либо пользователь не участвует, либо API вернул пусто")
        return None

    def _resolve_bid_id_from_trade_with_current_stage(
        self,
        *,
        session: requests.Session,
        trade_id: int,
        current_user_id: int | None = None,
    ) -> int | None:
        print(f"[PIPELINE] STEP 3: tradeWithCurrentStage for trade_id={trade_id}")
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
                body = self._post_graphql(
                    session=session,
                    endpoint=endpoint,
                    payload=payload,
                )
                bid_id = self._extract_bid_id_from_trade_with_current_stage_data(
                    body if isinstance(body, dict) else {},
                    current_user_id=current_user_id,
                    trade_id=trade_id,
                )
                print(f"[PIPELINE] STEP 3 DONE: trade_id={trade_id}, bid_id={bid_id}")
                return bid_id
            except Exception as exc:
                last_error = exc
                print(
                    "[PIPELINE] tradeWithCurrentStage attempt failed:",
                    endpoint,
                    str(exc),
                )

        if last_error is not None:
            print(
                f"[PIPELINE] Не удалось получить bid_id через tradeWithCurrentStage для trade_id={trade_id}: {last_error}"
            )
        return None

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

    def _export_with_lot_id(
        self,
        *,
        lot_id: int,
        target_path: Path,
        cookies: dict[str, str],
    ) -> str:
        lot_id_int = self._parse_positive_int(lot_id, name="lot_id")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self._headless)
            try:
                context = browser.new_context(accept_downloads=True)
                context.add_cookies(self._build_playwright_cookies(cookies))
                page = context.new_page()

                page.goto(
                    f"https://etp.metal-it.ru/bids/new?lot={lot_id_int}",
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

    @staticmethod
    def _write_retrade_debug_dump(page: Page) -> None:
        screenshot_path = Path("debug_retrade_open.png").resolve()
        html_path = Path("debug_retrade_open.html").resolve()
        try:
            page.screenshot(path=str(screenshot_path))
            print("[RETRADE] debug_screenshot:", str(screenshot_path))
        except Exception as exc:
            print("[RETRADE] debug_screenshot_error:", str(exc))
        try:
            html_path.write_text(page.content(), encoding="utf-8")
            print("[RETRADE] debug_html:", str(html_path))
        except Exception as exc:
            print("[RETRADE] debug_html_error:", str(exc))

    @staticmethod
    def _write_export_debug_dump(page: Page) -> None:
        screenshot_path = Path("export_debug.png").resolve()
        html_path = Path("export_debug.html").resolve()
        try:
            page.screenshot(path=str(screenshot_path))
            print("[RETRADE] export_screenshot:", str(screenshot_path))
        except Exception as exc:
            print("[RETRADE] export_screenshot_error:", str(exc))
        try:
            html_path.write_text(page.content(), encoding="utf-8")
            print("[RETRADE] export_html:", str(html_path))
        except Exception as exc:
            print("[RETRADE] export_html_error:", str(exc))

    @staticmethod
    def _write_retrade_open_dump(page: Page) -> None:
        screenshot_path = Path("retrade_open.png").resolve()
        html_path = Path("retrade_open.html").resolve()
        try:
            page.screenshot(path=str(screenshot_path))
            print("[RETRADE] open_screenshot:", str(screenshot_path))
        except Exception as exc:
            print("[RETRADE] open_screenshot_error:", str(exc))
        try:
            with open(html_path, "w", encoding="utf-8") as html_file:
                html_file.write(page.content())
            print("[RETRADE] open_html:", str(html_path))
        except Exception as exc:
            print("[RETRADE] open_html_error:", str(exc))

    @staticmethod
    def _is_probable_file_response_url(url: str) -> bool:
        url_lower = str(url or "").lower()
        return any(ext in url_lower for ext in (".xlsx", ".xls", "export", "download", "file"))

    @staticmethod
    def _is_probable_file_response_headers(headers: dict[str, str]) -> bool:
        content_type = str(headers.get("content-type", "")).lower()
        content_disposition = str(headers.get("content-disposition", "")).lower()
        if "attachment" in content_disposition:
            return True
        if any(
            marker in content_type
            for marker in (
                "spreadsheet",
                "excel",
                "octet-stream",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        ):
            return True
        return False

    def _download_via_requests(
        self,
        *,
        file_url: str,
        target_path: Path,
        cookies: dict[str, str],
        referer_url: str,
    ) -> None:
        session = requests.Session()
        try:
            session.headers.update(
                {
                    "Accept": "*/*",
                    "Referer": referer_url,
                    "Origin": self.BASE_URL,
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                }
            )
            for key, value in cookies.items():
                key_text = str(key).strip()
                value_text = str(value).strip()
                if not key_text or not value_text:
                    continue
                session.cookies.set(key_text, value_text, domain="etp.metal-it.ru", path="/")
                session.cookies.set(key_text, value_text)

            response = session.get(
                file_url,
                timeout=max(30.0, self._timeout_ms / 1000),
                stream=True,
                allow_redirects=True,
            )
            response.raise_for_status()
            content_type = str(response.headers.get("content-type", "")).lower()
            if "application/json" in content_type:
                raise RuntimeError("Сервер вернул JSON вместо файла")

            with target_path.open("wb") as output_file:
                for chunk in response.iter_content(chunk_size=65_536):
                    if chunk:
                        output_file.write(chunk)
            if target_path.stat().st_size <= 0:
                raise RuntimeError("Скачанный файл пустой")
        finally:
            session.close()

    def _try_download_via_network_fallback(
        self,
        *,
        candidate_urls: list[str],
        target_path: Path,
        cookies: dict[str, str],
        referer_url: str,
    ) -> bool:
        seen_urls: set[str] = set()
        ordered_candidates: list[str] = []
        for url in reversed(candidate_urls):
            url_text = str(url or "").strip()
            if not url_text or url_text in seen_urls:
                continue
            seen_urls.add(url_text)
            ordered_candidates.append(url_text)

        for file_url in ordered_candidates:
            if file_url.startswith("blob:"):
                continue
            try:
                self._download_via_requests(
                    file_url=file_url,
                    target_path=target_path,
                    cookies=cookies,
                    referer_url=referer_url,
                )
                print("[RETRADE] fallback_download_url:", file_url)
                return True
            except Exception as exc:
                print("[RETRADE] fallback_download_error:", str(exc))
        return False

    def _export_retrade_with_trade_id(
        self,
        *,
        trade_id: int,
        lot_id: int,
        selected_bid_id: int | None = None,
        target_path: Path,
        cookies: dict[str, str],
    ) -> str:
        lot_id_int = self._parse_positive_int(lot_id, name="lot_id")
        trade_id_int = self._parse_positive_int(trade_id, name="trade_id")
        retrade_timeout = max(self._timeout_ms, 60_000)
        api_session = self._build_api_session(cookies)
        stage_id: int | None = None
        bid_id: int | None = None
        final_target_path = target_path.with_name(f"retrade_{trade_id_int}.xlsx")

        try:
            stage_id = self._resolve_retrade_stage_id(
                session=api_session,
                trade_id=trade_id_int,
            )
            print(
                f"[PIPELINE] IDs: trade_id={trade_id_int}, lot_id={lot_id_int}, stage_id={stage_id}"
            )

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=self._headless)
                try:
                    context = browser.new_context(accept_downloads=True)
                    context.add_cookies(self._build_playwright_cookies(cookies))
                    page = context.new_page()

                    print(
                        "[PIPELINE] STEP 2: open stage page",
                        f"trade_id={trade_id_int}",
                        f"stage_id={stage_id}",
                    )
                    stage_url = open_retrading(
                        page,
                        trade_id=trade_id_int,
                        stage_id=stage_id,
                    )
                    print("[PIPELINE] STEP 2 URL:", page.url)
                    print("[PIPELINE] STEP 2 TITLE:", page.title())
                    if "login" in str(page.url).lower():
                        raise Exception("Playwright не авторизован")

                    if selected_bid_id is not None:
                        bid_id = self._parse_positive_int(
                            selected_bid_id,
                            name="bid_id",
                        )
                        print(f"[PIPELINE] STEP 3: используем выбранный bid_id={bid_id}")
                    else:
                        bids = get_trade_bids(page, trade_id_int)
                        if bids:
                            bid_id = self._parse_positive_int(
                                bids[0].get("bid_id"),
                                name="bid_id",
                            )
                            print(
                                f"[PIPELINE] STEP 3: выбран первый bid_id из /trades/{trade_id_int}: {bid_id}"
                            )
                    if bid_id is None:
                        print(f"Пропуск: нет участия в переторжке {trade_id_int}")
                        return ""
                    print(
                        f"[PIPELINE] IDs: trade_id={trade_id_int}, stage_id={stage_id}, bid_id={bid_id}"
                    )

                    target_url = f"{self.BASE_URL}/bids/{bid_id}/retrading"
                    print(f"[PIPELINE] STEP 4: open bid page {target_url}")
                    open_bid(page, bid_id)
                    current_url = page.url
                    current_title = page.title()
                    print("[RETRADE] url:", current_url)
                    print("[RETRADE] title:", current_title)
                    print("URL:", current_url)
                    print("TITLE:", current_title)
                    self._write_retrade_open_dump(page)
                    self._write_export_debug_dump(page)

                    if current_url.rstrip("/") != target_url.rstrip("/"):
                        print("Redirected to:", current_url)

                    spec_locator = page.locator("text=Спецификация")
                    access_denied_locator = page.locator("text=Доступ запрещен")
                    error_locator = page.locator("text=Ошибка")
                    no_access_locator = page.locator("text=Нет доступа")
                    spec_count = spec_locator.count()
                    access_denied_count = access_denied_locator.count()
                    error_count = error_locator.count()
                    no_access_count = no_access_locator.count()

                    print("Есть Спецификация:", spec_count)
                    print("Есть Доступ запрещен:", access_denied_count)
                    print("Есть Ошибка:", error_count)
                    print("Есть Нет доступа:", no_access_count)

                    if "login" in current_url.lower():
                        raise Exception("Playwright не авторизован")

                    if access_denied_count > 0 or no_access_count > 0:
                        raise Exception("Не удалось открыть страницу переторжки: нет доступа")

                    if spec_count == 0:
                        try:
                            page.wait_for_selector("text=Спецификация", timeout=20_000)
                            spec_count = spec_locator.count()
                        except Exception:
                            spec_count = spec_locator.count()

                    if spec_count == 0:
                        self._write_retrade_debug_dump(page)
                        if "login" in str(page.url).lower():
                            raise Exception("Playwright не авторизован")
                        if access_denied_locator.count() > 0 or no_access_locator.count() > 0:
                            raise Exception("Не удалось открыть страницу переторжки: нет доступа")
                        if error_locator.count() > 0:
                            raise Exception("Не удалось открыть страницу переторжки: страница вернула ошибку")
                        if str(page.url).rstrip("/") != target_url.rstrip("/"):
                            raise Exception("Не удалось открыть страницу переторжки: неправильный URL или редирект")
                        raise Exception("Не удалось открыть страницу переторжки: не найден блок 'Спецификация'")

                    print("[PIPELINE] STEP 6: export Excel")
                    export_button = page.locator("text=ЭКСПОРТ")
                    if export_button.count() == 0:
                        raise Exception("Кнопка ЭКСПОРТ не найдена")

                    candidate_urls: list[str] = []

                    def _collect_response(response: Any) -> None:
                        try:
                            response_url = str(response.url or "")
                            if response.status < 200 or response.status >= 400:
                                return
                            headers = {
                                str(key).lower(): str(value)
                                for key, value in dict(response.headers).items()
                            }
                            if (
                                self._is_probable_file_response_headers(headers)
                                or self._is_probable_file_response_url(response_url)
                            ):
                                candidate_urls.append(response_url)
                                print("[RETRADE] network_candidate:", response_url)
                        except Exception:
                            return

                    page.on("response", _collect_response)
                    try:
                        try:
                            with page.expect_download(timeout=30_000) as download_info:
                                export_button.first.click()
                            download = download_info.value
                            download.save_as(str(final_target_path))
                            print("Файл сохранен:", str(final_target_path))
                        except Exception as exc:
                            print("[RETRADE] expect_download_error:", str(exc))
                            fallback_ok = self._try_download_via_network_fallback(
                                candidate_urls=candidate_urls,
                                target_path=final_target_path,
                                cookies=cookies,
                                referer_url=page.url,
                            )
                            if not fallback_ok:
                                self._write_export_debug_dump(page)
                                raise Exception("Не удалось скачать файл через кнопку ЭКСПОРТ") from exc
                            print("Файл сохранен:", str(final_target_path))
                    finally:
                        try:
                            page.remove_listener("response", _collect_response)
                        except Exception:
                            pass
                finally:
                    browser.close()
        except Exception as exc:
            print(
                "[PIPELINE] ERROR:",
                f"trade_id={trade_id_int}",
                f"stage_id={stage_id}",
                f"bid_id={bid_id}",
                str(exc),
            )
            raise
        finally:
            api_session.close()

        return str(final_target_path.resolve())

    def export_lot_data(self, lot_id: int, download_path: str) -> str:
        lot_id_int = self._parse_positive_int(lot_id, name="lot_id")
        target_path = self._validate_target_path(download_path)
        cookies = self._load_cookies_for_export()
        return self._export_with_lot_id(
            lot_id=lot_id_int,
            target_path=target_path,
            cookies=cookies,
        )

    def export_trade_data(self, trade_id: int, download_path: str) -> str:
        trade_id_int = self._parse_positive_int(trade_id, name="trade_id")
        target_path = self._validate_target_path(download_path)
        cookies = self._load_cookies_for_export()

        lot_id = self._resolve_lot_id_from_api(trade_id=trade_id_int, cookies=cookies)
        return self._export_with_lot_id(
            lot_id=lot_id,
            target_path=target_path,
            cookies=cookies,
        )

    def export_retrade_lot_data(
        self,
        lot_id: int,
        download_path: str,
        *,
        trade_id: int | None = None,
        bid_id: int | None = None,
    ) -> str:
        if bid_id is not None:
            return self.export_retrade_bid_data(
                bid_id=bid_id,
                download_path=download_path,
            )

        lot_id_int = self._parse_positive_int(lot_id, name="lot_id")
        if trade_id is None:
            raise Exception("Не указан trade_id для открытия страницы переторжки")
        target_path = self._validate_target_path(download_path)
        cookies = self._load_cookies_for_export()
        return self._export_retrade_with_trade_id(
            trade_id=trade_id,
            lot_id=lot_id_int,
            selected_bid_id=bid_id,
            target_path=target_path,
            cookies=cookies,
        )

    def export_retrade_bid_data(
        self,
        *,
        bid_id: int,
        download_path: str,
    ) -> str:
        bid_id_int = self._parse_positive_int(bid_id, name="bid_id")
        target_path = self._validate_target_path(download_path)
        cookies = self._load_cookies_for_export()

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self._headless)
            try:
                context = browser.new_context(accept_downloads=True)
                context.add_cookies(self._build_playwright_cookies(cookies))
                page = context.new_page()
                saved_path = export_retrading_table(
                    page,
                    bid_id=bid_id_int,
                    download_dir="./downloads",
                )
            finally:
                browser.close()

        return saved_path

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
