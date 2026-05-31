import unittest
from pathlib import Path
from tempfile import NamedTemporaryFile

import submission.submission_playwright as submission_playwright_module
from submission.submission_playwright import SubmissionPlaywright
from submission.submission_service import SubmissionHeader, SubmissionPayload


class _FakeElement:
    def __init__(
        self,
        *,
        visible=True,
        enabled=True,
        attrs=None,
        fill_error=None,
        text="",
    ):
        self.visible = visible
        self.enabled = enabled
        self.attrs = dict(attrs or {})
        self.fill_error = fill_error
        self._text = str(text)
        self.clicked = False
        self.scrolled = False
        self.dispatched = False
        self.files = []
        self.filled_value = None
        self.selected_options = []

    def is_visible(self, timeout=None):
        return self.visible

    def is_enabled(self, timeout=None):
        return self.enabled

    def scroll_into_view_if_needed(self, timeout=None):
        self.scrolled = True

    def click(self, *args, **kwargs):
        self.clicked = True

    def dispatch_event(self, event):
        self.dispatched = event == "click"

    def set_input_files(self, files):
        self.files = [str(files)]

    def fill(self, value, timeout=None):
        if self.fill_error is not None:
            raise self.fill_error
        self.filled_value = value

    def select_option(self, **kwargs):
        self.selected_options.append(kwargs)

    def get_attribute(self, name):
        return self.attrs.get(name)

    def inner_text(self, timeout=None):
        return self._text

    def text_content(self, timeout=None):
        return self._text

    def wait_for(self, *_args, **_kwargs):
        return None


class _FakeLocator:
    def __init__(self, elements=None):
        self.elements = list(elements or [])

    @property
    def first(self):
        return self.nth(0)

    def count(self):
        return len(self.elements)

    def nth(self, index):
        return self.elements[index]


class _FakePage:
    def __init__(self, locators=None):
        self.locators = dict(locators or {})
        self.waited = False

    def locator(self, selector):
        return _FakeLocator(self.locators.get(selector, []))

    def get_by_label(self, *_args, **_kwargs):
        return _FakeLocator(self.locators.get("get_by_label", []))

    def get_by_placeholder(self, *_args, **_kwargs):
        return _FakeLocator(self.locators.get("get_by_placeholder", []))

    def get_by_role(self, *_args, **_kwargs):
        return _FakeLocator()

    def wait_for_timeout(self, *_args, **_kwargs):
        self.waited = True

    def wait_for_load_state(self, *_args, **_kwargs):
        return None

    def wait_for_function(self, *_args, **_kwargs):
        return None

    def evaluate(self, *_args, **_kwargs):
        return ["Сохранить черновик", "Вернуться на страницу торгов"]

    def content(self):
        return "<html></html>"

    def screenshot(self, **_kwargs):
        return None


class _FakeNavigationPage(_FakePage):
    def __init__(self, locators=None):
        super().__init__(locators)
        self.goto_calls = []

    def goto(self, url, **kwargs):
        self.goto_calls.append({"url": url, "kwargs": kwargs})


class SubmissionPlaywrightTests(unittest.TestCase):
    def test_click_submit_finds_material_link_button(self):
        button = _FakeElement()
        page = _FakePage(
            {
                "a.um-links-main-link:has-text('Подать предложение')": [button],
            }
        )
        submitter = SubmissionPlaywright({"JSESSIONID": "cookie"}, allow_submit=True)

        submitter._click_submit(page)

        self.assertTrue(button.clicked)
        self.assertTrue(button.scrolled)
        self.assertTrue(page.waited)

    def test_click_submit_finds_register_offer_button(self):
        button = _FakeElement()
        page = _FakePage(
            {
                "a.um-links-main-link:has-text('Зарегистрировать предложение')": [button],
            }
        )
        submitter = SubmissionPlaywright({"JSESSIONID": "cookie"}, allow_submit=True)

        submitter._click_submit(page)

        self.assertTrue(button.clicked)

    def test_click_submit_falls_back_to_title_button(self):
        button = _FakeElement()
        page = _FakePage(
            {
                "[title*='Подать предложение' i]": [button],
            }
        )
        submitter = SubmissionPlaywright({"JSESSIONID": "cookie"}, allow_submit=True)

        submitter._click_submit(page)

        self.assertTrue(button.clicked)

    def test_click_submit_error_includes_visible_actions(self):
        page = _FakePage()
        submitter = SubmissionPlaywright({"JSESSIONID": "cookie"}, allow_submit=True)
        submitter._save_debug_artifacts = lambda *_args, **_kwargs: None

        with self.assertRaisesRegex(RuntimeError, "Сохранить черновик"):
            submitter._click_submit(page)

    def test_submission_url_uses_hidden_lot_id(self):
        payload = SubmissionPayload(
            header=SubmissionHeader(number="125475", title="Заявка", lot_id="557621478"),
            rows=[],
        )

        self.assertEqual(
            SubmissionPlaywright._submission_url_from_payload(payload),
            "https://etp.metal-it.ru/bids/new?lot=557621478",
        )

    def test_submission_url_rejects_registered_number_without_lot_id(self):
        payload = SubmissionPayload(
            header=SubmissionHeader(number="125475", title="Заявка"),
            rows=[],
        )

        with self.assertRaisesRegex(ValueError, "Не найден lot_id"):
            SubmissionPlaywright._submission_url_from_payload(payload)

    def test_goto_submission_page_prefers_trade_page_when_trade_id_available(self):
        payload = SubmissionPayload(
            header=SubmissionHeader(
                trade_id="777",
                number="125475",
                title="Заявка",
                lot_id="557621478",
            ),
            rows=[],
        )
        page = _FakeNavigationPage({"button:has-text('Импорт')": [_FakeElement()]})
        submitter = SubmissionPlaywright({"JSESSIONID": "cookie"}, allow_submit=True)

        submitter._goto_submission_page_for_payload(page, payload)

        self.assertEqual(len(page.goto_calls), 1)
        self.assertEqual(
            page.goto_calls[0]["url"],
            "https://etp.metal-it.ru/trades/777",
        )

    def test_goto_submission_page_uses_direct_lot_route_without_trade_id(self):
        payload = SubmissionPayload(
            header=SubmissionHeader(number="125475", title="Заявка", lot_id="557621478"),
            rows=[],
        )
        page = _FakeNavigationPage()
        submitter = SubmissionPlaywright({"JSESSIONID": "cookie"}, allow_submit=True)

        submitter._goto_submission_page_for_payload(page, payload)

        self.assertEqual(len(page.goto_calls), 1)
        self.assertEqual(
            page.goto_calls[0]["url"],
            "https://etp.metal-it.ru/bids/new?lot=557621478",
        )

    def test_import_submission_file_uses_excel_import_input(self):
        file_input = _FakeElement()
        page = _FakePage(
            {
                "kendo-grid-toolbar um-excel-import input[type='file']": [file_input],
            }
        )
        submitter = SubmissionPlaywright({"JSESSIONID": "cookie"}, allow_submit=True)

        with NamedTemporaryFile(suffix=".xlsx") as tmp_file:
            submitter._import_submission_file(page, Path(tmp_file.name))

        self.assertEqual(file_input.files, [tmp_file.name])

    def test_select_submission_currency_skips_when_already_selected(self):
        select = _FakeElement(text="CNY")
        page = _FakePage({"um-select-field.field_currency mat-select": [select]})
        submitter = SubmissionPlaywright({"JSESSIONID": "cookie"}, allow_submit=True)

        self.assertTrue(submitter._select_submission_currency(page, "юани"))
        self.assertFalse(select.clicked)

    def test_select_submission_currency_uses_currency_dropdown(self):
        select = _FakeElement(text="RUB")
        option = _FakeElement(text="CNY")
        page = _FakePage(
            {
                "um-select-field.field_currency mat-select": [select],
                ".cdk-overlay-container mat-option:has-text('CNY')": [option],
            }
        )
        submitter = SubmissionPlaywright({"JSESSIONID": "cookie"}, allow_submit=True)

        self.assertTrue(submitter._select_submission_currency(page, "CNY"))
        self.assertTrue(select.clicked)
        self.assertTrue(option.clicked)
        self.assertTrue(page.waited)

    def test_validate_import_file_rejects_non_excel(self):
        with NamedTemporaryFile(suffix=".txt") as tmp_file:
            with self.assertRaisesRegex(ValueError, "Excel файл"):
                SubmissionPlaywright._validate_import_file_path(tmp_file.name)

    def test_submit_default_mode_is_blocked_without_allow_submit(self):
        payload = SubmissionPayload(
            header=SubmissionHeader(number="125475", title="Заявка", lot_id="557621478"),
            rows=[],
        )
        old_sync_playwright = submission_playwright_module.sync_playwright
        submission_playwright_module.sync_playwright = lambda: None
        try:
            submitter = SubmissionPlaywright({"JSESSIONID": "cookie"}, allow_submit=False)
            with NamedTemporaryFile(suffix=".xlsx") as tmp_file:
                with self.assertRaisesRegex(PermissionError, "allow_submit=False"):
                    submitter.submit(payload, import_file_path=tmp_file.name)
        finally:
            submission_playwright_module.sync_playwright = old_sync_playwright

    def test_normalize_offer_validity_period_accepts_common_date_formats(self):
        self.assertEqual(
            SubmissionPlaywright._normalize_offer_validity_period("2026-12-31"),
            "31.12.2026",
        )
        self.assertEqual(
            SubmissionPlaywright._normalize_offer_validity_period("31/12/2026"),
            "31.12.2026",
        )

    def test_fill_delivery_order_uses_visible_labeled_field(self):
        field = _FakeElement()
        page = _FakePage(
            {
                "mat-form-field:has-text('Порядок доставки') input:not([type='checkbox']):not([type='radio']):not([type='file'])": [field],
            }
        )
        submitter = SubmissionPlaywright({"JSESSIONID": "cookie"}, allow_submit=True)

        self.assertTrue(submitter._fill_delivery_order(page, "До склада"))
        self.assertEqual(field.filled_value, "До склада")

    def test_fill_payment_terms_uses_visible_labeled_field(self):
        field = _FakeElement()
        page = _FakePage(
            {
                "mat-form-field:has-text('Условие оплаты') input:not([type='checkbox']):not([type='radio']):not([type='file'])": [field],
            }
        )
        submitter = SubmissionPlaywright({"JSESSIONID": "cookie"}, allow_submit=True)

        self.assertTrue(submitter._fill_payment_terms(page, "Оплата по договору"))
        self.assertEqual(field.filled_value, "Оплата по договору")

    def test_fill_payment_terms_skips_switch_label_match(self):
        switch = _FakeElement(
            attrs={"type": "checkbox", "role": "switch", "aria-checked": "false"},
            fill_error=RuntimeError('Input of type "checkbox" cannot be filled'),
        )
        field = _FakeElement()
        page = _FakePage(
            {
                "get_by_label": [switch],
                "mat-form-field:has-text('Условия оплаты') input:not([type='checkbox']):not([type='radio']):not([type='file'])": [field],
            }
        )
        submitter = SubmissionPlaywright({"JSESSIONID": "cookie"}, allow_submit=True)

        self.assertTrue(submitter._fill_payment_terms(page, "10 рабочих дней"))
        self.assertIsNone(switch.filled_value)
        self.assertEqual(field.filled_value, "10 рабочих дней")


if __name__ == "__main__":
    unittest.main()
