from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import BrowserContext, Download, Locator, Page, sync_playwright


def _save_debug_artifacts(page: Page, *, prefix: str = "export_debug") -> None:
    Path(f"{prefix}.html").write_text(page.content(), encoding="utf-8")
    page.screenshot(path=f"{prefix}.png", full_page=True)


def _log_buttons(page: Page) -> None:
    print("Все кнопки на странице:")
    buttons = page.locator("button")
    count = buttons.count()
    for index in range(count):
        try:
            text = (buttons.nth(index).inner_text() or "").strip()
            if text:
                print("-", text)
        except Exception:
            pass


def _resolve_export_button(page: Page) -> tuple[Locator, int]:
    candidate = page.locator("button:has-text('Экспорт'), a:has-text('Экспорт')")
    count = candidate.count()
    if count == 0:
        fallback = page.locator("text=Экспорт")
        count = fallback.count()
        return fallback.first, count
    return candidate.first, count


def _download_with_force_click(page: Page, export_button: Locator) -> Download:
    with page.expect_download(timeout=60_000) as download_info:
        export_button.click(force=True)
    return download_info.value


def _download_with_js_click(page: Page, export_button: Locator) -> Download:
    handle = export_button.element_handle(timeout=10_000)
    if handle is None:
        raise RuntimeError("Не удалось получить element_handle для кнопки Экспорт")
    with page.expect_download(timeout=60_000) as download_info:
        page.evaluate("(el) => el.click()", handle)
    return download_info.value


def _download_with_hard_fallback(page: Page) -> Download:
    with page.expect_download(timeout=60_000) as download_info:
        page.evaluate(
            """
            () => {
                const btn = Array.from(document.querySelectorAll('button, a'))
                    .find(el => (el.innerText || '').includes('Экспорт'));
                if (btn) {
                    btn.click();
                }
            }
            """
        )
    return download_info.value


def export_retrading_table(page: Page, context: BrowserContext, bid_id: int, save_path: str) -> str:
    del context

    bid_id_int = int(bid_id)
    if bid_id_int <= 0:
        raise ValueError(f"Некорректный bid_id: {bid_id_int}")

    url = f"https://etp.metal-it.ru/bids/{bid_id_int}/retrading"
    print("[DEBUG] открытие страницы:", url)

    response_urls: list[str] = []

    def _on_download(download: Download) -> None:
        print("🔥 Download event:", download.suggested_filename)

    def _on_response(response) -> None:
        response_url = str(getattr(response, "url", "") or "")
        response_urls.append(response_url)
        print("[RESPONSE]", response_url)

    page.on("download", _on_download)
    page.on("response", _on_response)

    try:
        page.goto(url, timeout=60_000)
        page.wait_for_load_state("networkidle", timeout=60_000)
        page.wait_for_timeout(5000)

        print("Страница загружена:", page.url)
        print("Текущий URL:", page.url)
        page.wait_for_selector("text=Экспорт", timeout=60_000)

        export_button, count = _resolve_export_button(page)
        print(f"Найдено кнопок Экспорт: {count}")

        if count == 0:
            print("HTML страницы:")
            print(page.content())
            _save_debug_artifacts(page, prefix="export_error")
            raise Exception("❌ Кнопка Экспорт НЕ найдена")

        _log_buttons(page)

        export_button.scroll_into_view_if_needed()
        page.wait_for_timeout(1000)

        print("Ожидаем скачивание файла...")

        download: Download | None = None

        try:
            download = _download_with_force_click(page, export_button)
        except Exception as click_error:
            print("❌ Обычный клик не сработал:", click_error)

            try:
                print("Пробуем JS click...")
                download = _download_with_js_click(page, export_button)
            except Exception as js_error:
                print("❌ JS click не сработал:", js_error)
                print("Пробуем жесткий fallback click...")
                download = _download_with_hard_fallback(page)

        if download is None:
            raise RuntimeError("Download объект не получен")

        filename = str(download.suggested_filename or f"retrading_{bid_id_int}.xlsx")
        target_path = Path(save_path).expanduser().resolve() if save_path else Path(f"retrading_{bid_id_int}.xlsx").resolve()
        target_path.parent.mkdir(parents=True, exist_ok=True)

        download.save_as(str(target_path))

        print(f"✅ Файл скачан: {target_path}")
        print(f"📄 Имя файла: {filename}")
        _save_debug_artifacts(page, prefix="export_debug")
        return str(target_path)
    except Exception:
        print("[DEBUG] response urls:")
        for response_url in response_urls:
            print("-", response_url)
        _save_debug_artifacts(page, prefix="export_error")
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
            page = context.new_page()

            for bid_id in bid_ids:
                bid_id_int = int(bid_id)
                target_file = exports_path / f"retrading_{bid_id_int}.xlsx"
                try:
                    saved_file = export_retrading_table(
                        page,
                        context,
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
