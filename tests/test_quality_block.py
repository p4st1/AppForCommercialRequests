import tempfile
import unittest
from pathlib import Path

from config import Config
from database import Database
from tools import DatabaseTools as Tool


class QualityBlockTests(unittest.TestCase):
    def setUp(self):
        self._original_log_path = Config.log_path
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.log_path = Path(self.temp_dir.name) / "quality.log"
        Config.log_path = str(self.log_path)

    def tearDown(self):
        Config.log_path = self._original_log_path

    def _read_log(self) -> str:
        if not self.log_path.exists():
            return ""
        return self.log_path.read_text(encoding="utf-8")

    def test_write_log_writes_into_configured_file(self):
        Tool.write_log("log-line-check")
        content = self._read_log()
        self.assertIn("log-line-check", content)

    def test_log_exception_writes_context_and_traceback(self):
        try:
            raise RuntimeError("boom")
        except RuntimeError as error:
            Tool.log_exception("unit-test-error", error, include_traceback=True)

        content = self._read_log()
        self.assertIn("[ERROR] unit-test-error: RuntimeError: boom", content)
        self.assertIn("Traceback (most recent call last)", content)

    def test_database_open_failure_is_logged(self):
        db = Database()
        bad_path = Path(self.temp_dir.name) / "missing-dir" / "database.db"

        status = db.open(str(bad_path))

        self.assertEqual(status, -1)
        content = self._read_log()
        self.assertIn("Не удалось открыть БД", content)
        self.assertIn(str(bad_path), content)


if __name__ == "__main__":
    unittest.main()
