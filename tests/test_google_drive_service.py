import tempfile
import unittest
from pathlib import Path

from config import Config
from services.google_drive_service import GoogleDriveService


class GoogleDriveServiceTests(unittest.TestCase):
    def setUp(self):
        self._old_config = Config.config.copy()

    def tearDown(self):
        Config.config = self._old_config

    def test_is_configured_requires_existing_credentials_file(self):
        Config.config["googleDriveCredentialsPath"] = "/tmp/missing-client.json"
        self.assertFalse(GoogleDriveService.is_configured())

        with tempfile.TemporaryDirectory() as temp_dir:
            credentials_path = Path(temp_dir) / "client.json"
            credentials_path.write_text("{}", encoding="utf-8")
            Config.config["googleDriveCredentialsPath"] = str(credentials_path)
            self.assertTrue(GoogleDriveService.is_configured())

    def test_folder_id_is_trimmed(self):
        Config.config["googleDriveFolderId"] = "  folder-123  "
        self.assertEqual(GoogleDriveService.folder_id(), "folder-123")

    def test_validate_client_secrets_file_rejects_empty_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            credentials_path = Path(temp_dir) / "client.json"
            credentials_path.write_text("", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "пустой"):
                GoogleDriveService._validate_client_secrets_file(credentials_path)

    def test_validate_client_secrets_file_rejects_wrong_shape(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            credentials_path = Path(temp_dir) / "client.json"
            credentials_path.write_text('{"type":"service_account"}', encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "Desktop app"):
                GoogleDriveService._validate_client_secrets_file(credentials_path)

    def test_validate_client_secrets_file_accepts_desktop_client_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            credentials_path = Path(temp_dir) / "client.json"
            credentials_path.write_text('{"installed":{}}', encoding="utf-8")
            GoogleDriveService._validate_client_secrets_file(credentials_path)


if __name__ == "__main__":
    unittest.main()
