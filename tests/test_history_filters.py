import tempfile
import unittest
from pathlib import Path

from database import Database


class HistoryFilterTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.db_path = Path(self.temp_dir.name) / "history.db"
        self.db = Database()
        status = self.db.open(str(self.db_path))
        self.assertEqual(status, 0)
        self._insert_history_rows()

    def tearDown(self):
        self.db.close()

    def _insert_history_rows(self):
        self.db.cursor.executemany(
            """
            INSERT INTO offers (
                offer_number,
                date,
                created_at,
                event_type,
                customer_company,
                customer_name,
                items_count,
                total_amount,
                currency,
                file_path,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (
                    1,
                    "2026-05-18",
                    "2026-05-18 12:00:00",
                    "docx",
                    'ООО "ШСУ"',
                    "Аксёнова Эльвира",
                    2,
                    55109.92,
                    "¥",
                    "/tmp/kp_125864.docx",
                    "",
                ),
                (
                    2,
                    "2026-05-14",
                    "2026-05-14 11:00:00",
                    "docx",
                    'ООО "ИванЗолото"',
                    "Иванов Иван",
                    27,
                    1097539.18,
                    "¥",
                    "/tmp/kp_125133.docx",
                    "",
                ),
                (
                    0,
                    "2026-05-14",
                    "2026-05-14 10:00:00",
                    "excel",
                    "",
                    "",
                    27,
                    1097539.18,
                    "¥",
                    "/tmp/raschety_125133.xlsx",
                    "Экспорт расчетной таблицы",
                ),
            ),
        )
        self.db.save()

    def test_filters_by_customer_event_and_dates(self):
        rows = self.db.getOffersHistory(
            customer_query="ШСУ",
            event_type="docx",
            date_from="2026-05-18",
            date_to="2026-05-18",
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][5], 'ООО "ШСУ"')
        self.assertEqual(rows[0][4], "docx")

    def test_search_matches_file_path_and_notes(self):
        file_rows = self.db.getOffersHistory(search_text="125133.xlsx")
        notes_rows = self.db.getOffersHistory(search_text="расчетной")

        self.assertEqual(len(file_rows), 1)
        self.assertEqual(file_rows[0][4], "excel")
        self.assertEqual(len(notes_rows), 1)
        self.assertEqual(notes_rows[0][4], "excel")


if __name__ == "__main__":
    unittest.main()
