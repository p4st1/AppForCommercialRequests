from __future__ import annotations

import json
import re
from pathlib import Path

from playwright.sync_api import BrowserContext, Download, Locator, Page, sync_playwright


def _save_debug_artifacts(page: Page, *, prefix: str = "export_debug") -> None:
    Path(f"{prefix}.html").write_text(page.content(), encoding="utf-8")
    page.screenshot(path=f"{prefix}.png", full_page=True)


def _safe_page_title(page: Page) -> str:
    try:
        return str(page.title() or "")
    except Exception:
        return ""


def _print_first_button_texts(page: Page, *, limit: int = 20) -> None:
    print(f"BUTTON TEXTS (first {limit}):")
    buttons = page.locator("button")
    total = buttons.count()
    for index in range(min(total, limit)):
        try:
            text = (buttons.nth(index).inner_text() or "").strip()
        except Exception:
            text = ""
        print(f"- [{index}] {text}")


def _emit_failure_diagnostics(page: Page, *, response_urls: list[str]) -> None:
    print("CURRENT URL:", page.url)
    print("PAGE TITLE:", _safe_page_title(page))
    _print_first_button_texts(page, limit=20)
    print("RESPONSE URLS:")
    for response_url in response_urls:
        print("-", response_url)
    _save_debug_artifacts(page, prefix="export_debug")


def resolve_retrading_page(
    context: BrowserContext,
    bid_id: int,
    preferred_page: Page | None = None,
) -> Page:
    bid_id_int = int(bid_id)
    if bid_id_int <= 0:
        raise ValueError(f"Некорректный bid_id: {bid_id_int}")

    fragment = f"/bids/{bid_id_int}/retrading"
    target_url = f"https://etp.metal-it.ru{fragment}"

    if preferred_page is not None:
        try:
            if fragment in str(preferred_page.url or ""):
                return preferred_page
        except Exception:
            pass

    for candidate in context.pages:
        try:
            if fragment in str(candidate.url or ""):
                return candidate
        except Exception:
            continue

    page = context.new_page()
    page.goto(target_url, timeout=60_000)
    page.wait_for_load_state("networkidle", timeout=60_000)
    return page


def _validate_retrading_page(page: Page, *, bid_id: int) -> None:
    bid_id_int = int(bid_id)
    fragment = f"/bids/{bid_id_int}/retrading"
    if fragment not in str(page.url or ""):
        _save_debug_artifacts(page, prefix="export_debug")
        raise RuntimeError("Экспорт выполняется не на странице переторжки")

    markers = (
        re.compile(r"Переторжка\s+по\s+лоту", re.IGNORECASE),
        re.compile(r"Предложение\s+участника", re.IGNORECASE),
        re.compile(r"ЗАРЕГИСТРИРОВАТЬ\s+ПРЕДЛОЖЕНИЕ", re.IGNORECASE),
    )
    has_marker = False
    for marker in markers:
        if page.get_by_text(marker).count() > 0:
            has_marker = True
            break

    if not has_marker:
        _save_debug_artifacts(page, prefix="export_debug")
        raise RuntimeError("Открыта не страница переторжки")


def _first_visible_variant(variant: Locator, *, max_items: int = 50) -> Locator | None:
    count = variant.count()
    for index in range(min(count, max_items)):
        candidate = variant.nth(index)
        try:
            if candidate.is_visible():
                return candidate
        except Exception:
            continue
    return None


def _resolve_export_button(page: Page) -> Locator | None:
    variants = [
        page.get_by_role("button", name=re.compile("экспорт", re.IGNORECASE)),
        page.locator("button:has-text('Экспорт')"),
        page.locator("a:has-text('Экспорт')"),
        page.locator("[aria-label*='Экспорт' i]"),
        page.locator("[title*='Экспорт' i]"),
        page.locator("mat-icon, svg").locator(".."),
    ]

    for variant in variants:
        candidate = _first_visible_variant(variant)
        if candidate is not None:
            return candidate
    return None


def _download_with_click(page: Page, locator: Locator) -> Download:
    try:
        with page.expect_download(timeout=30_000) as download_info:
            locator.click(force=True)
        return download_info.value
    except Exception as first_error:
        print("❌ Обычный клик не сработал:", first_error)
        with page.expect_download(timeout=30_000) as download_info:
            handle = locator.element_handle(timeout=10_000)
            if handle is None:
                raise RuntimeError("Не удалось получить element_handle для JS click")
            page.evaluate("(el) => el.click()", handle)
        return download_info.value


def export_retrading_table(
    context: BrowserContext,
    bid_id: int,
    save_path: str,
    preferred_page: Page | None = None,
) -> str:
    bid_id_int = int(bid_id)
    if bid_id_int <= 0:
        raise ValueError(f"Некорректный bid_id: {bid_id_int}")

    page = resolve_retrading_page(context, bid_id_int, preferred_page=preferred_page)
    response_urls: list[str] = []

    def _on_download(download: Download) -> None:
        print("[DOWNLOAD EVENT]", download.suggested_filename)

    def _on_response(response) -> None:
        response_url = str(getattr(response, "url", "") or "")
        response_urls.append(response_url)
        print("[RESPONSE]", response_url)

    page.on("download", _on_download)
    page.on("response", _on_response)

    try:
        page.wait_for_load_state("networkidle", timeout=60_000)
        page.wait_for_timeout(5000)

        print("Страница загружена:", page.url)
        _validate_retrading_page(page, bid_id=bid_id_int)

        export_button = _resolve_export_button(page)
        if export_button is None:
            raise RuntimeError("Кнопка Экспорт НЕ найдена")

        export_button.scroll_into_view_if_needed()
        page.wait_for_timeout(1000)

        print("Ожидаем скачивание файла...")
        download = _download_with_click(page, export_button)

        filename = str(download.suggested_filename or f"retrading_{bid_id_int}.xlsx")
        target_path = Path(save_path).expanduser().resolve()
        target_path.parent.mkdir(parents=True, exist_ok=True)

        download.save_as(str(target_path))
        print(f"✅ Файл скачан: {target_path}")
        print(f"📄 Имя файла: {filename}")
        return str(target_path)
    except Exception:
        _emit_failure_diagnostics(page, response_urls=response_urls)
        raise
    finally:
        try:
            page.remove_listener("download", _on_download)
        except Exception:
            pass
        try:
            page.remove_listener("response", _on_response)
        except Exception:
            pass


def export_all(
    bid_ids: list[int],
    *,
    storage_state_path: str = "storage_state.json",
    exports_dir: str = "exports",
    headless: bool = True,
) -> dict[int, str]:
    if not bid_ids:
        return {}

    exports_path = Path(exports_dir).expanduser().resolve()
    exports_path.mkdir(parents=True, exist_ok=True)

    storage_state = Path(storage_state_path).expanduser().resolve()
    if not storage_state.exists():
        raise FileNotFoundError(
            f"Не найден storage state с авторизацией: {storage_state}. "
            "Сохраните state из Playwright и повторите."
        )

    results: dict[int, str] = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        try:
            context = browser.new_context(storage_state=str(storage_state), accept_downloads=True)

            for bid_id in bid_ids:
                bid_id_int = int(bid_id)
                target_file = exports_path / f"retrading_{bid_id_int}.xlsx"
                try:
                    saved_file = export_retrading_table(
                        context=context,
                        bid_id=bid_id_int,
                        save_path=str(target_file),
                    )
                    results[bid_id_int] = saved_file
                except Exception as exc:
                    print(f"[ERROR] bid_id={bid_id_int}: {exc}")
                    error_payload = {"bid_id": bid_id_int, "error": str(exc)}
                    with Path("export_debug.log").open("a", encoding="utf-8") as log_file:
                        log_file.write(json.dumps(error_payload, ensure_ascii=False) + "\n")
        finally:
            browser.close()

    return results
