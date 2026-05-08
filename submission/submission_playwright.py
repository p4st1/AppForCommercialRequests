from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .submission_service import FIELD_LABELS, FIELD_ORDER, SubmissionPayload

try:
    from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright
except (ImportError, ModuleNotFoundError):  # pragma: no cover - optional runtime dependency
    Page = Any  # type: ignore[assignment]
    PlaywrightTimeoutError = TimeoutError  # type: ignore[assignment]
    sync_playwright = None  # type: ignore[assignment]


class SubmissionPlaywright:
    BASE_URL = "https://etp.metal-it.ru"
    TRADE_URL_TEMPLATE = "https://etp.metal-it.ru/trades/{trade_id}"
    SUBMISSION_URL_TEMPLATE = "https://etp.metal-it.ru/bids/new?lot={lot_id}"

    def __init__(
        self,
        cookies: dict[str, str],
        *,
        headless: bool = False,
        allow_submit: bool = False,
        timeout_ms: int = 90_000,
    ) -> None:
        self._cookies = self._normalize_cookies(cookies)
        if not self._cookies:
            raise ValueError("Не найдены cookies для авторизации")
        self._headless = bool(headless)
        self._allow_submit = bool(allow_submit)
        self._timeout_ms = int(timeout_ms)

    @staticmethod
    def _normalize_cookies(raw: Any) -> dict[str, str]:
        if not isinstance(raw, dict):
            return {}
        cookies: dict[str, str] = {}
        for key, value in raw.items():
            key_text = str(key or "").strip()
            value_text = str(value or "").strip()
            if key_text and value_text:
                cookies[key_text] = value_text
        return cookies

    def _build_playwright_cookies(self) -> list[dict[str, str]]:
        return [
            {
                "name": name,
                "value": value,
                "url": self.BASE_URL,
            }
            for name, value in self._cookies.items()
        ]

    @staticmethod
    def _positive_int_from_value(value: Any, *, name: str) -> int:
        text = str(value or "").strip()
        if not text:
            raise ValueError(f"Не указан {name}")
        match = re.fullmatch(r"\d+", text)
        if match is None:
            raise ValueError(f"{name} должен быть числом")
        number = int(match.group(0))
        if number <= 0:
            raise ValueError(f"Некорректный {name}: {number}")
        return number

    @classmethod
    def _trade_id_from_number(cls, number: Any) -> int:
        text = str(number or "").strip()
        match = re.search(r"\d+", text)
        if match is None:
            raise ValueError("Номер заявки должен содержать ID площадки")
        return cls._positive_int_from_value(match.group(0), name="trade_id")

    @classmethod
    def _lot_id_from_payload(cls, payload: SubmissionPayload) -> int:
        header = payload.header
        lot_id = str(getattr(header, "lot_id", "") or "").strip()
        if lot_id:
            return cls._positive_int_from_value(lot_id, name="lot_id")

        number_text = str(getattr(header, "number", "") or "").strip()
        explicit_match = re.search(
            r"(?:lot|лот|lot_id)\D*(\d+)",
            number_text,
            re.IGNORECASE,
        )
        if explicit_match is not None:
            return cls._positive_int_from_value(explicit_match.group(1), name="lot_id")

        if re.fullmatch(r"\d{7,}", number_text):
            return cls._positive_int_from_value(number_text, name="lot_id")

        raise ValueError(
            "Не найден lot_id для подачи заявки. "
            "Загрузите заявку через кнопку 'Экспорт' из таблицы приема заявок "
            "или укажите lot_id явно."
        )

    @classmethod
    def _submission_url_from_payload(cls, payload: SubmissionPayload) -> str:
        lot_id = cls._lot_id_from_payload(payload)
        return cls.SUBMISSION_URL_TEMPLATE.format(lot_id=lot_id)

    @staticmethod
    def _page_has_submission_import(page: Page) -> bool:
        for selector in (
            "kendo-grid-toolbar um-excel-import input[type='file']",
            "um-excel-import input[type='file']",
            "kendo-grid-toolbar button:has-text('Импорт')",
            "button:has-text('Импорт')",
        ):
            try:
                if page.locator(selector).count() > 0:
                    return True
            except Exception:
                continue
        return False

    def _goto_submission_page(self, page: Page, submission_url: str) -> None:
        try:
            page.goto(
                submission_url,
                wait_until="domcontentloaded",
                timeout=self._timeout_ms,
            )
            return
        except PlaywrightTimeoutError as exc:
            if self._page_has_submission_import(page):
                return

            try:
                page.goto(
                    submission_url,
                    wait_until="commit",
                    timeout=max(15_000, self._timeout_ms // 2),
                )
                return
            except Exception:
                if self._page_has_submission_import(page):
                    return
                self._save_debug_artifacts(page, "submission_open_timeout")
                raise RuntimeError(
                    "Не удалось открыть страницу подачи заявки. "
                    "Площадка не ответила вовремя."
                ) from exc

    @staticmethod
    def _validate_import_file_path(import_file_path: str | Path | None) -> Path:
        if import_file_path is None:
            raise ValueError(
                "Не найден Excel файл для импорта. "
                "Сначала выгрузите заявку через кнопку 'Экспорт'."
            )
        source_path = Path(import_file_path).expanduser()
        if source_path.suffix.lower() not in {".xlsx", ".xls"}:
            raise ValueError("Для подачи заявки нужен Excel файл площадки (.xlsx/.xls)")
        if not source_path.exists() or not source_path.is_file():
            raise FileNotFoundError(f"Excel файл для импорта не найден: {source_path}")
        return source_path.resolve()

    def submit(
        self,
        payload: SubmissionPayload,
        *,
        import_file_path: str | Path | None = None,
    ) -> str:
        if sync_playwright is None:
            raise RuntimeError("Playwright недоступен в текущем окружении")
        if not self._allow_submit:
            raise PermissionError(
                "Подача заявки заблокирована: allow_submit=False. "
                "Подтвердите действие в интерфейсе перед отправкой."
            )

        submission_url = self._submission_url_from_payload(payload)
        import_path = self._validate_import_file_path(import_file_path)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self._headless)
            try:
                context = browser.new_context()
                context.add_cookies(self._build_playwright_cookies())
                page = context.new_page()
                self._goto_submission_page(page, submission_url)

                self._wait_for_submission_import_ready(page)
                self._import_submission_file(page, import_path)
                self._fill_offer_validity_period(
                    page,
                    getattr(payload.header, "offer_validity_period", ""),
                )
                self._click_submit(page)
                self._wait_for_success(page)
            finally:
                browser.close()

        return f"Заявка {payload.header.number} подана"

    def _open_submission_form(self, page: Page) -> None:
        candidates = (
            "button:has-text('Подать заявку')",
            "button:has-text('Подать предложение')",
            "button:has-text('Создать заявку')",
            "a:has-text('Подать заявку')",
            "a:has-text('Подать предложение')",
            "[role='button']:has-text('Подать заявку')",
            "[role='button']:has-text('Подать предложение')",
        )
        for selector in candidates:
            locator = page.locator(selector).first
            try:
                if locator.count() > 0 and locator.is_visible(timeout=1_000):
                    locator.click(timeout=4_000)
                    page.wait_for_timeout(1_000)
                    return
            except PlaywrightTimeoutError:
                continue

    def _fill_header(self, page: Page, payload: SubmissionPayload) -> None:
        header_fields = (
            (("Номер заявки", "Номер", "trade number"), payload.header.number),
            (("Название заявки", "Название", "title"), payload.header.title),
            (("Заказчик", "customer"), payload.header.customer),
            (("Валюта", "currency"), payload.header.currency),
        )
        for labels, value in header_fields:
            if str(value or "").strip():
                self._fill_first_matching_field(page, labels, value)

    def _fill_rows(self, page: Page, payload: SubmissionPayload) -> None:
        for row_index, row in enumerate(payload.rows):
            self._ensure_position_row(page, row_index)
            row_values = row.to_cells()
            for field, value in zip(FIELD_ORDER, row_values, strict=True):
                if field == "total":
                    continue
                self._fill_position_field(
                    page,
                    row_index=row_index,
                    label=FIELD_LABELS[field],
                    value=value,
                )

    def _ensure_position_row(self, page: Page, row_index: int) -> None:
        if row_index == 0:
            return
        selectors = (
            "button:has-text('Добавить позицию')",
            "button:has-text('Добавить строку')",
            "button[aria-label*='Добавить']",
        )
        for selector in selectors:
            locator = page.locator(selector).first
            try:
                if locator.count() > 0 and locator.is_visible(timeout=700):
                    locator.click(timeout=3_000)
                    page.wait_for_timeout(500)
                    return
            except PlaywrightTimeoutError:
                continue

    def _fill_first_matching_field(
        self,
        page: Page,
        labels: tuple[str, ...],
        value: Any,
    ) -> bool:
        text_value = "" if value is None else str(value)
        for label in labels:
            locators = (
                page.get_by_label(re.compile(re.escape(label), re.IGNORECASE)).first,
                page.get_by_placeholder(re.compile(re.escape(label), re.IGNORECASE)).first,
                page.locator(f"input[name*='{label}' i]").first,
                page.locator(f"textarea[name*='{label}' i]").first,
            )
            for locator in locators:
                try:
                    if locator.count() == 0 or not locator.is_visible(timeout=500):
                        continue
                    locator.fill(text_value, timeout=3_000)
                    return True
                except PlaywrightTimeoutError:
                    continue
        return False

    def _fill_position_field(
        self,
        page: Page,
        *,
        row_index: int,
        label: str,
        value: Any,
    ) -> bool:
        text_value = "" if value is None else str(value)
        if not text_value.strip():
            return False

        row_candidates = (
            page.locator("table tbody tr").nth(row_index),
            page.locator("[role='row']").nth(row_index + 1),
            page.locator(".mat-row").nth(row_index),
        )
        for row_locator in row_candidates:
            try:
                if row_locator.count() == 0:
                    continue
                field = row_locator.get_by_label(
                    re.compile(re.escape(label), re.IGNORECASE)
                ).first
                if field.count() > 0:
                    field.fill(text_value, timeout=3_000)
                    return True
                placeholder = row_locator.get_by_placeholder(
                    re.compile(re.escape(label), re.IGNORECASE)
                ).first
                if placeholder.count() > 0:
                    placeholder.fill(text_value, timeout=3_000)
                    return True
            except PlaywrightTimeoutError:
                continue

        labels = (label, label.lower(), label.replace(" ", ""))
        return self._fill_first_matching_field(page, labels, text_value)

    @staticmethod
    def _normalize_offer_validity_period(value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            return ""

        date_part = text.split()[0].strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(date_part, fmt).strftime("%d.%m.%Y")
            except ValueError:
                continue
        return date_part

    def _fill_offer_validity_period(self, page: Page, value: Any) -> bool:
        text_value = self._normalize_offer_validity_period(value)
        if not text_value:
            return False

        locators = (
            page.locator("um-date-time-field")
            .filter(has_text=re.compile("Срок действия КП", re.IGNORECASE))
            .locator("input.date, input.mat-datepicker-input, input")
            .first,
            page.locator("mat-form-field")
            .filter(has_text=re.compile("Срок действия КП", re.IGNORECASE))
            .locator("input")
            .first,
            page.get_by_label(re.compile("Срок действия КП", re.IGNORECASE)).first,
        )
        for locator in locators:
            try:
                if locator.count() == 0:
                    continue
                locator.fill(text_value, timeout=4_000)
                try:
                    locator.press("Tab", timeout=1_000)
                except Exception:
                    pass
                return True
            except Exception:
                continue

        return False

    def _wait_for_submission_import_ready(self, page: Page) -> None:
        try:
            page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            pass

        ready_selectors = (
            "kendo-grid-toolbar um-excel-import input[type='file']",
            "um-excel-import input[type='file']",
            "kendo-grid-toolbar button:has-text('Импорт')",
            "button:has-text('Импорт')",
        )
        last_error: Exception | None = None
        for selector in ready_selectors:
            try:
                page.locator(selector).first.wait_for(state="attached", timeout=8_000)
                return
            except Exception as exc:
                last_error = exc
                continue
        raise RuntimeError("Кнопка 'Импорт' не найдена на странице подачи заявки") from last_error

    def _find_submission_import_file_input(self, page: Page) -> Any:
        selectors = (
            "kendo-grid-toolbar um-excel-import input[type='file']",
            "um-excel-import input[type='file']",
            "input[type='file']",
        )
        for selector in selectors:
            locator = page.locator(selector)
            try:
                if locator.count() > 0:
                    return locator.first
            except Exception:
                continue
        raise RuntimeError("Поле выбора Excel файла для импорта не найдено")

    def _find_submission_import_button(self, page: Page) -> Any:
        selectors = (
            "kendo-grid-toolbar um-excel-import button:has-text('Импорт')",
            "um-excel-import button:has-text('Импорт')",
            "kendo-grid-toolbar button:has-text('Импорт')",
            "button:has-text('Импорт')",
            "[role='button']:has-text('Импорт')",
        )
        for selector in selectors:
            locator = page.locator(selector)
            try:
                if locator.count() > 0:
                    return locator.first
            except Exception:
                continue
        raise RuntimeError("Кнопка 'Импорт' не найдена на странице подачи заявки")

    def _import_submission_file(self, page: Page, import_path: Path) -> None:
        try:
            file_input = self._find_submission_import_file_input(page)
            file_input.set_input_files(str(import_path))
        except Exception:
            import_button = self._find_submission_import_button(page)
            try:
                with page.expect_file_chooser(timeout=10_000) as chooser_info:
                    self._click_first_visible_enabled(import_button, label="Импорт")
                chooser_info.value.set_files(str(import_path))
            except Exception as exc:
                self._save_debug_artifacts(page, "submission_import_button_error")
                raise RuntimeError("Не удалось выбрать Excel файл через кнопку 'Импорт'") from exc

        page.wait_for_timeout(1_000)
        self._click_import_confirmation_if_present(page)
        self._wait_for_import_completion(page)

    def _click_import_confirmation_if_present(self, page: Page) -> None:
        for text in ("Подтвердить", "Загрузить", "Импорт", "ОК", "Да"):
            for selector in (
                f"mat-dialog-container button:has-text('{text}')",
                f".cdk-overlay-container button:has-text('{text}')",
                f"[role='dialog'] button:has-text('{text}')",
            ):
                if self._click_first_visible_enabled(page.locator(selector), label=text):
                    page.wait_for_timeout(500)
                    return

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

    def _wait_for_import_completion(self, page: Page) -> None:
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
                raise RuntimeError(f"Площадка вернула ошибку при импорте: {text}")

    def _click_submit(self, page: Page) -> None:
        for locator, label in self._submit_locator_candidates(page):
            if self._click_first_visible_enabled(locator, label=label):
                page.wait_for_timeout(800)
                self._click_confirmation_if_present(page)
                page.wait_for_timeout(500)
                return

        self._save_debug_artifacts(page, "submission_submit_button_not_found")
        diagnostics = self._visible_action_diagnostics(page)
        details = f" Видимые действия на странице: {diagnostics}" if diagnostics else ""
        raise RuntimeError(f"Не найдена финальная кнопка подачи заявки.{details}")

    @staticmethod
    def _submit_texts() -> tuple[str, ...]:
        return (
            "Зарегистрировать предложение",
            "Зарегистрировать заявку",
            "Подать предложение",
            "Подать заявку",
            "Отправить заявку",
            "Отправить предложение",
            "Отправить",
            "Подтвердить подачу",
            "Подтвердить",
        )

    @classmethod
    def _submit_selectors(cls, text: str) -> tuple[str, ...]:
        return (
            f"a.um-links-main-link:has-text('{text}')",
            f".toolbar__right a:has-text('{text}')",
            f"um-links a:has-text('{text}')",
            f"a.mat-flat-button:has-text('{text}')",
            f"a.mat-stroked-button:has-text('{text}')",
            f"a[mat-stroked-button]:has-text('{text}')",
            f"button:has-text('{text}')",
            f"a:has-text('{text}')",
            f"[role='button']:has-text('{text}')",
            f"[aria-label*='{text}' i]",
            f"[title*='{text}' i] button",
            f"[title*='{text}' i]",
        )

    def _submit_locator_candidates(self, page: Page) -> list[tuple[Any, str]]:
        candidates: list[tuple[Any, str]] = []
        for text in self._submit_texts():
            pattern = re.compile(re.escape(text), re.IGNORECASE)
            for role in ("button", "link"):
                try:
                    candidates.append((page.get_by_role(role, name=pattern), text))
                except Exception:
                    pass
            for selector in self._submit_selectors(text):
                candidates.append((page.locator(selector), text))
        return candidates

    def _click_first_visible_enabled(self, locator: Any, *, label: str) -> bool:
        try:
            count = locator.count()
        except Exception:
            return False

        for index in range(min(count, 10)):
            try:
                candidate = locator.nth(index)
                if not candidate.is_visible(timeout=700):
                    continue
                if not candidate.is_enabled(timeout=700):
                    continue
                candidate.scroll_into_view_if_needed(timeout=3_000)
                try:
                    candidate.click(timeout=4_000)
                except PlaywrightTimeoutError:
                    try:
                        candidate.click(force=True, timeout=4_000)
                    except PlaywrightTimeoutError:
                        candidate.dispatch_event("click")
                print("CLICK:", label)
                return True
            except PlaywrightTimeoutError:
                continue
            except Exception:
                continue
        return False

    def _click_confirmation_if_present(self, page: Page) -> None:
        confirmation_texts = (
            "Подтвердить",
            "Зарегистрировать",
            "Зарегистрировать предложение",
            "Да",
            "ОК",
            "Подать",
            "Подать предложение",
            "Отправить",
        )
        for text in confirmation_texts:
            for selector in (
                f"mat-dialog-container button:has-text('{text}')",
                f".cdk-overlay-container button:has-text('{text}')",
                f"[role='dialog'] button:has-text('{text}')",
            ):
                if self._click_first_visible_enabled(page.locator(selector), label=text):
                    page.wait_for_timeout(500)
                    return

    @staticmethod
    def _visible_action_diagnostics(page: Page) -> str:
        try:
            items = page.evaluate(
                """
                () => Array.from(
                    document.querySelectorAll('button,a,[role="button"],.mat-button-base')
                )
                    .filter((element) => {
                        const style = window.getComputedStyle(element);
                        const rect = element.getBoundingClientRect();
                        return style.visibility !== 'hidden'
                            && style.display !== 'none'
                            && rect.width > 0
                            && rect.height > 0;
                    })
                    .map((element) => [
                        element.innerText,
                        element.getAttribute('title'),
                        element.getAttribute('aria-label'),
                    ].filter(Boolean).join(' | ').replace(/\\s+/g, ' ').trim())
                    .filter(Boolean)
                    .slice(0, 25)
                """
            )
        except Exception:
            return ""
        if not isinstance(items, list):
            return ""
        unique: list[str] = []
        for item in items:
            text = str(item or "").strip()
            if text and text not in unique:
                unique.append(text)
        return "; ".join(unique[:15])

    @staticmethod
    def _save_debug_artifacts(page: Page, prefix: str) -> None:
        try:
            target_dir = Path("temp") / "submission"
            target_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            html_path = target_dir / f"{prefix}_{timestamp}.html"
            html_path.write_text(page.content(), encoding="utf-8")
            try:
                page.screenshot(
                    path=str(target_dir / f"{prefix}_{timestamp}.png"),
                    full_page=True,
                )
            except Exception:
                pass
            print("DEBUG:", str(html_path.resolve()))
        except Exception:
            pass

    def _wait_for_success(self, page: Page) -> None:
        page.wait_for_timeout(2_000)
        success_patterns = (
            re.compile(r"успеш", re.IGNORECASE),
            re.compile(r"заявк.*подан", re.IGNORECASE),
            re.compile(r"предложени.*подан", re.IGNORECASE),
            re.compile(r"отправ", re.IGNORECASE),
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

        raise RuntimeError("Не удалось подтвердить подачу заявки на странице")
