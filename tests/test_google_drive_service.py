import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from config import Config
from services.google_drive_service import GoogleDriveService
from utilities import paths


class _FakeDriveRequest:
    def __init__(self, result):
        self._result = result

    def execute(self):
        return self._result


class _FakeFilesResource:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(("create", kwargs))
        body = kwargs.get("body", {})
        return _FakeDriveRequest(
            {
                "id": "file-id",
                "name": body.get("name", "uploaded.file"),
                "webViewLink": "https://drive.google.com/file/d/file-id/view",
            }
        )

    def update(self, **kwargs):
        self.calls.append(("update", kwargs))
        return _FakeDriveRequest(
            {
                "id": kwargs.get("fileId", "file-id"),
                "name": "updated.file",
                "webViewLink": "https://drive.google.com/file/d/file-id/view",
            }
        )


class _FakePermissionsResource:
    def __init__(self, list_result=None):
        self.calls = []
        self.list_result = list_result if list_result is not None else {"permissions": []}

    def list(self, **kwargs):
        self.calls.append(("list", kwargs))
        return _FakeDriveRequest(self.list_result)

    def create(self, **kwargs):
        self.calls.append(("create", kwargs))
        return _FakeDriveRequest({"id": "anyone-permission", **kwargs.get("body", {})})

    def update(self, **kwargs):
        self.calls.append(("update", kwargs))
        return _FakeDriveRequest({"id": kwargs.get("permissionId"), **kwargs.get("body", {})})


class _FakeDrive:
    def __init__(self, permissions_result=None):
        self.files_resource = _FakeFilesResource()
        self.permissions_resource = _FakePermissionsResource(permissions_result)

    def files(self):
        return self.files_resource

    def permissions(self):
        return self.permissions_resource


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

    def test_upload_docx_sets_anyone_with_link_writer_permission(self):
        fake_drive = _FakeDrive()

        def fake_build(*_args, **_kwargs):
            return fake_drive

        def fake_media_file_upload(*_args, **_kwargs):
            return SimpleNamespace()

        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "offer.docx"
            source_path.write_text("docx", encoding="utf-8")

            service = GoogleDriveService()
            with patch.object(service, "_load_credentials", return_value=SimpleNamespace()):
                with patch.object(
                    service,
                    "_load_drive_client_symbols",
                    return_value=(fake_build, fake_media_file_upload, None),
                ):
                    service.upload_docx(source_path)

        self.assertEqual(fake_drive.permissions_resource.calls[0][0], "list")
        create_call = fake_drive.permissions_resource.calls[1]
        self.assertEqual(create_call[0], "create")
        self.assertEqual(create_call[1]["fileId"], "file-id")
        self.assertEqual(
            create_call[1]["body"],
            {
                "type": "anyone",
                "role": "writer",
                "allowFileDiscovery": False,
            },
        )

    def test_existing_anyone_permission_is_updated_to_writer(self):
        fake_drive = _FakeDrive(
            {
                "permissions": [
                    {
                        "id": "anyone-permission",
                        "type": "anyone",
                        "role": "reader",
                        "allowFileDiscovery": False,
                    }
                ]
            }
        )

        GoogleDriveService()._ensure_anyone_with_link_can_edit(fake_drive, "file-id")

        update_call = fake_drive.permissions_resource.calls[1]
        self.assertEqual(update_call[0], "update")
        self.assertEqual(update_call[1]["fileId"], "file-id")
        self.assertEqual(update_call[1]["permissionId"], "anyone-permission")
        self.assertEqual(
            update_call[1]["body"],
            {
                "role": "writer",
                "allowFileDiscovery": False,
            },
        )

    def test_update_excel_refreshes_anyone_with_link_writer_permission(self):
        fake_drive = _FakeDrive(
            {
                "permissions": [
                    {
                        "id": "anyone-permission",
                        "type": "anyone",
                        "role": "reader",
                        "allowFileDiscovery": False,
                    }
                ]
            }
        )

        def fake_build(*_args, **_kwargs):
            return fake_drive

        def fake_media_file_upload(*_args, **_kwargs):
            return SimpleNamespace()

        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "calculations.xlsx"
            source_path.write_text("xlsx", encoding="utf-8")

            service = GoogleDriveService()
            with patch.object(service, "_load_credentials", return_value=SimpleNamespace()):
                with patch.object(
                    service,
                    "_load_drive_client_symbols",
                    return_value=(fake_build, fake_media_file_upload, None),
                ):
                    service.update_excel("file-id", source_path)

        self.assertEqual(fake_drive.files_resource.calls[0][0], "update")
        self.assertEqual(fake_drive.permissions_resource.calls[0][0], "list")
        update_call = fake_drive.permissions_resource.calls[1]
        self.assertEqual(update_call[0], "update")
        self.assertEqual(update_call[1]["fileId"], "file-id")
        self.assertEqual(update_call[1]["permissionId"], "anyone-permission")
        self.assertEqual(
            update_call[1]["body"],
            {
                "role": "writer",
                "allowFileDiscovery": False,
            },
        )


if __name__ == "__main__":
    unittest.main()
