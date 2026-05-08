import tempfile
import unittest
from pathlib import Path

from retrade.retrade_service import RetradeService


class RetradeServiceTests(unittest.TestCase):
    def test_validate_excel_path_accepts_excel_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "retrade.xlsx"
            file_path.write_bytes(b"placeholder")

            context = RetradeService.validate_excel_path(file_path, bid_id="123")

        self.assertEqual(context.bid_id, 123)
        self.assertEqual(context.file_path.name, "retrade.xlsx")

    def test_validate_excel_path_rejects_non_excel_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "offer.docx"
            file_path.write_bytes(b"placeholder")

            with self.assertRaisesRegex(ValueError, "только с Excel"):
                RetradeService.validate_excel_path(file_path, bid_id=123)


if __name__ == "__main__":
    unittest.main()
