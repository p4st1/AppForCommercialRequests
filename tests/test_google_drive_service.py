import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from config import Config
from services.google_drive_service import GoogleDriveService
from utilities import paths


class GoogleDriveServiceTests(unittest.TestCase):
    def setUp(self):
        self._old_config = Config.config.copy()
        self._old_user_data_dir = os.environ.get("MYAPP_USER_DATA_DIR")
        paths.user_data_dir.cache_clear()

    def tearDown(self):
        Config.config = self._old_config
        if self._old_user_data_dir is None:
            os.environ.pop("MYAPP_USER_DATA_DIR", None)
        else:
            os.environ["MYAPP_USER_DATA_DIR"] = self._old_user_data_dir
        paths.user_data_dir.cache_clear()

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

    def test_extract_file_id_accepts_common_drive_links(self):
        self.assertEqual(
            GoogleDriveService.extract_file_id(
                "https://drive.google.com/file/d/abc_DEF-12345/view?usp=sharing"
            ),
            "abc_DEF-12345",
        )
        self.assertEqual(
            GoogleDriveService.extract_file_id(
                "https://docs.google.com/spreadsheets/d/sheet_ID-987/edit#gid=0"
            ),
            "sheet_ID-987",
        )
        self.assertEqual(
            GoogleDriveService.extract_file_id(
                "https://drive.google.com/open?id=open_ID-12345"
            ),
            "open_ID-12345",
        )
        self.assertEqual(
            GoogleDriveService.extract_file_id("raw_ID-12345"),
            "raw_ID-12345",
        )

    def test_delete_saved_authorization_removes_token_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ["MYAPP_USER_DATA_DIR"] = temp_dir
            paths.user_data_dir.cache_clear()
            token_path = GoogleDriveService.token_path()
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text("{}", encoding="utf-8")

            self.assertTrue(GoogleDriveService.delete_saved_authorization())
            self.assertFalse(token_path.exists())

    def test_auth_error_reset_deletes_token_and_prompts_reauth(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ["MYAPP_USER_DATA_DIR"] = temp_dir
            paths.user_data_dir.cache_clear()
            token_path = GoogleDriveService.token_path()
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text("{}", encoding="utf-8")

            exc = RuntimeError("invalid_grant")
            self.assertTrue(GoogleDriveService._is_google_authorization_error(exc))
            with self.assertRaisesRegex(RuntimeError, "заново войдите"):
                GoogleDriveService()._reset_saved_authorization_after_error(exc)
            self.assertFalse(token_path.exists())

    def test_http_401_is_auth_error(self):
        exc = SimpleNamespace(resp=SimpleNamespace(status=401))
        self.assertTrue(GoogleDriveService._is_google_authorization_error(exc))


if __name__ == "__main__":
    unittest.main()
