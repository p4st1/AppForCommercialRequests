import tempfile
import unittest
from pathlib import Path

from submission.submission_service import (
    SubmissionHeader,
    SubmissionRow,
    SubmissionService,
)


class SubmissionServiceTests(unittest.TestCase):
    def test_validate_requires_final_submission_fields(self):
        service = SubmissionService()
        header = SubmissionHeader(
            number="123",
            title="Тестовая заявка",
            offer_validity_period="31.12.2026",
        )
        rows = [
            SubmissionRow(
                name="Насос",
                qty=2,
                unit="шт",
                unit_price=100,
                delivery_time="30 дней",
                manufacturer="Atlas Copco",
                technical="Техописание",
            ),
            SubmissionRow(name="Клапан", qty=1),
        ]

        issues = service.validate(header, rows)

        errors = [(issue.row, issue.label) for issue in issues if issue.severity == "error"]
        warnings = [(issue.row, issue.label) for issue in issues if issue.severity == "warning"]
        self.assertEqual(errors, [])
        self.assertIn((1, "Цена за ед."), warnings)
        self.assertIn((1, "Срок поставки"), warnings)
        self.assertIn((1, "Производитель"), warnings)
        self.assertIn((1, "Технические характеристики"), warnings)
        self.assertIn((0, "Статус поставщика"), warnings)
        self.assertIn((0, "Гарантия"), warnings)

    def test_validate_keeps_missing_header_fields_blocking(self):
        service = SubmissionService()

        issues = service.validate(SubmissionHeader(), [SubmissionRow(name="Насос")])

        errors = [issue.label for issue in issues if issue.severity == "error"]
        self.assertIn("Номер заявки", errors)
        self.assertIn("Название заявки", errors)
        self.assertIn("Срок действия КП", errors)

    def test_prepare_payload_calculates_total(self):
        payload = SubmissionService.prepare_payload(
            SubmissionHeader(
                number="REQ-1",
                title="Заявка",
                offer_validity_period="31.12.2026",
                delivery_order="Доставка до склада",
                payment_terms="Оплата по договору",
            ),
            [
                SubmissionRow(name="Насос", qty="2", unit_price="100,50"),
                SubmissionRow(name=""),
            ],
        )

        self.assertEqual(len(payload.rows), 1)
        self.assertEqual(payload.rows[0].total, 201.0)
        self.assertEqual(payload.header.total, 201.0)
        self.assertEqual(payload.header.offer_validity_period, "31.12.2026")
        self.assertEqual(payload.header.delivery_order, "Доставка до склада")
        self.assertEqual(payload.header.payment_terms, "Оплата по договору")

    def test_prepare_payload_infers_currency_from_row_price(self):
        payload = SubmissionService.prepare_payload(
            SubmissionHeader(
                number="REQ-1",
                title="Заявка",
                offer_validity_period="31.12.2026",
            ),
            [
                SubmissionRow(
                    name="Насос",
                    qty="2",
                    unit_price="146.36 ¥",
                    delivery_time="30 дней",
                    manufacturer="cat",
                    technical="гидромотор",
                )
            ],
        )

        self.assertEqual(payload.header.currency, "CNY")
        self.assertEqual(payload.rows[0].unit_price, 146.36)
        self.assertEqual(payload.rows[0].total, 292.72)

    def test_parse_number_accepts_currency_codes_and_names(self):
        self.assertEqual(SubmissionService.parse_number("1 234,50 CNY"), 1234.5)
        self.assertEqual(SubmissionService.parse_number("1 234,50 тенге"), 1234.5)
        self.assertEqual(SubmissionService.parse_number("1 234,50 рублей"), 1234.5)

    def test_rows_from_matrix_detects_headers(self):
        rows = SubmissionService._rows_from_matrix(
            [
                ["Наименование", "Кол-во", "Ед. изм.", "Цена за ед.", "Срок поставки"],
                ["Насос", "2", "шт", "100", "30 дней"],
            ]
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].name, "Насос")
        self.assertEqual(rows[0].qty, 2.0)
        self.assertEqual(rows[0].unit_price, 100.0)
        self.assertEqual(rows[0].total, 200.0)

    def test_rows_from_matrix_prefers_name_over_alternative_name(self):
        rows = SubmissionService._rows_from_matrix(
            [
                [
                    "Наименование",
                    "Ед. изм.",
                    "Кол-во",
                    "Предлагаемая цена за ед. (без учета НДС)",
                    "Альтернативное наименование",
                ],
                ["Насос", "шт", "1", "123", ""],
            ]
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].name, "Насос")
        self.assertEqual(rows[0].unit_price, 123.0)

    def test_rows_from_matrix_splits_semicolon_rows(self):
        rows = SubmissionService._rows_from_matrix(
            [
                ["№;Наименование;Каталожный номер;Ед.изм.;Кол-во;Цена за ед. без НДС;Срок поставки"],
                ["1;Насос;P-1;шт;2;100;30 дней"],
            ]
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].name, "Насос")
        self.assertEqual(rows[0].unit, "шт")
        self.assertEqual(rows[0].qty, 2.0)
        self.assertEqual(rows[0].unit_price, 100.0)
        self.assertEqual(rows[0].delivery_time, "30 дней")

    def test_currency_from_matrix_detects_export_header_code(self):
        currency = SubmissionService._currency_from_matrix(
            [
                [
                    "Наименование",
                    "Предлагаемая цена за ед. (без учета НДС)",
                    "Сумма, CNY (без учета НДС)",
                ],
                ["Насос", "100", "200"],
            ]
        )

        self.assertEqual(currency, "CNY")

    def test_normalize_currency_code_accepts_symbols_and_names(self):
        self.assertEqual(SubmissionService.normalize_currency_code("рубли"), "RUB")
        self.assertEqual(SubmissionService.normalize_currency_code("1 000,00 ₽"), "RUB")
        self.assertEqual(SubmissionService.normalize_currency_code("юани"), "CNY")
        self.assertEqual(SubmissionService.normalize_currency_code("CYN"), "CNY")
        self.assertEqual(SubmissionService.normalize_currency_code("USD"), "USD")

    def test_load_csv_detects_semicolon_delimiter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "submission.csv"
            file_path.write_text(
                "№;Наименование;Ед. изм.;Кол-во;Цена за ед.;Срок поставки\n"
                "1;Клапан;шт;3;50;10 дней\n",
                encoding="utf-8",
            )

            rows = SubmissionService.load_kp(file_path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].name, "Клапан")
        self.assertEqual(rows[0].qty, 3.0)
        self.assertEqual(rows[0].total, 150.0)

    def test_save_payload_writes_json(self):
        payload = SubmissionService.prepare_payload(
            SubmissionHeader(number="REQ-1", title="Заявка"),
            [SubmissionRow(name="Насос", qty=2, unit_price=100)],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            saved_path = SubmissionService.save_payload(payload, tmpdir)

            self.assertTrue(Path(saved_path).exists())
            self.assertIn("submission_REQ-1", Path(saved_path).name)


if __name__ == "__main__":
    unittest.main()
