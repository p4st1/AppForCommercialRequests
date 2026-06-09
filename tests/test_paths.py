import os
import tempfile
import unittest
from pathlib import Path

from utilities import paths


class AppDataPathTests(unittest.TestCase):
    def setUp(self):
        self._old_override = os.environ.get("MYAPP_USER_DATA_DIR")
        paths.user_data_dir.cache_clear()

    def tearDown(self):
        if self._old_override is None:
            os.environ.pop("MYAPP_USER_DATA_DIR", None)
        else:
            os.environ["MYAPP_USER_DATA_DIR"] = self._old_override
        paths.user_data_dir.cache_clear()

    def test_user_data_dir_uses_override_and_user_path_stays_inside_it(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            override = Path(tmp_dir) / "AppData"
            os.environ["MYAPP_USER_DATA_DIR"] = str(override)
            paths.user_data_dir.cache_clear()

            user_dir = paths.user_data_dir()

            self.assertEqual(user_dir.resolve(), override.resolve())
            self.assertTrue(user_dir.is_dir())
            self.assertEqual(
                paths.user_path("database", "database.db"),
                user_dir / "database" / "database.db",
            )


if __name__ == "__main__":
    unittest.main()
