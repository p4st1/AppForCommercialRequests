from __future__ import annotations

import io
import json
import re
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from config import Config
from utilities.paths import user_path, user_subdir


@dataclass(frozen=True)
class GoogleDriveUploadResult:
    file_id: str
    name: str
    web_view_link: str


@dataclass(frozen=True)
class GoogleDriveDownloadResult:
    file_id: str
    name: str
    local_path: Path
    web_view_link: str


class GoogleDriveService:
    SCOPES = ("https://www.googleapis.com/auth/drive",)
    OAUTH_CALLBACK_HOST = "127.0.0.1"
    OAUTH_CALLBACK_TIMEOUT_SECONDS = 300
    DOCX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    XLSX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    GOOGLE_SHEETS_MIME_TYPE = "application/vnd.google-apps.spreadsheet"
    TOKEN_FILE_NAME = "google_drive_token.json"
    LINK_EDITOR_PERMISSION = {
        "type": "anyone",
        "role": "writer",
        "allowFileDiscovery": False,
    }

    @classmethod
    def credentials_path(cls) -> Path | None:
        raw_path = str(Config.config.get("googleDriveCredentialsPath", "") or "").strip()
        if not raw_path:
            return None
        return Path(raw_path).expanduser()

    @classmethod
    def folder_id(cls) -> str:
        return str(Config.config.get("googleDriveFolderId", "") or "").strip()

    @classmethod
    def token_path(cls) -> Path:
        return user_path(cls.TOKEN_FILE_NAME)

    @classmethod
    def delete_saved_authorization(cls) -> bool:
        token_path = cls.token_path()
        existed = token_path.exists()
        try:
            token_path.unlink(missing_ok=True)
        except OSError as exc:
            raise RuntimeError(
                f"Не удалось удалить сохраненную авторизацию Google Drive: {token_path}"
            ) from exc
        return existed

    @classmethod
    def is_configured(cls) -> bool:
        credentials_path = cls.credentials_path()
        return credentials_path is not None and credentials_path.is_file()

    @staticmethod
    def extract_file_id(link_or_file_id: str) -> str:
        text = str(link_or_file_id or "").strip()
        if not text:
            return ""

        parsed = urlparse(text)
        if parsed.scheme and parsed.netloc:
            query_id = parse_qs(parsed.query).get("id", [""])[0].strip()
            if query_id:
                return query_id

            match = re.search(r"/(?:file|spreadsheets)/d/([^/]+)", parsed.path)
            if match:
                return match.group(1).strip()

            match = re.search(r"/d/([^/]+)", parsed.path)
            if match:
                return match.group(1).strip()
            return ""

        if re.fullmatch(r"[A-Za-z0-9_-]{10,}", text):
            return text
        return ""

    @staticmethod
    def file_web_view_link(file_id: str) -> str:
        normalized_file_id = str(file_id or "").strip()
        return f"https://drive.google.com/file/d/{normalized_file_id}/view"

    def upload_docx(self, file_path: str | Path) -> GoogleDriveUploadResult:
        return self._upload_file(
            file_path,
            mimetype=self.DOCX_MIME_TYPE,
            missing_label="DOCX",
        )

    def upload_excel(self, file_path: str | Path) -> GoogleDriveUploadResult:
        return self._upload_file(
            file_path,
            mimetype=self.XLSX_MIME_TYPE,
            missing_label="XLSX",
        )

    def download_excel(
        self,
        link_or_file_id: str,
        *,
        destination_dir: str | Path | None = None,
    ) -> GoogleDriveDownloadResult:
        file_id = self.extract_file_id(link_or_file_id)
        if not file_id:
            raise ValueError("Укажите корректную ссылку или id файла Google Drive")

        credentials = self._load_credentials()
        build, _media_file_upload, media_io_base_download = (
            self._load_drive_client_symbols()
        )
        drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
        metadata = self._execute_drive_request(
            drive.files().get(
                fileId=file_id,
                fields="id,name,mimeType,webViewLink",
            ),
            "получения файла Google Drive",
        )

        file_name = str(metadata.get("name") or f"drive_{file_id}.xlsx").strip()
        mime_type = str(metadata.get("mimeType") or "").strip()
        if mime_type.startswith("application/vnd.google-apps.") and (
            mime_type != self.GOOGLE_SHEETS_MIME_TYPE
        ):
            raise RuntimeError("Google Drive файл должен быть таблицей или XLSX")

        if not file_name.lower().endswith((".xlsx", ".xlsm", ".xls")):
            file_name = f"{file_name}.xlsx"

        if destination_dir is None:
            target_dir = user_subdir("temp", "retrade", "drive")
        else:
            target_dir = Path(destination_dir).expanduser()
            target_dir.mkdir(parents=True, exist_ok=True)
        destination_path = target_dir / self._safe_download_name(file_name)

        if mime_type == self.GOOGLE_SHEETS_MIME_TYPE:
            request = drive.files().export_media(
                fileId=file_id,
                mimeType=self.XLSX_MIME_TYPE,
            )
        else:
            request = drive.files().get_media(fileId=file_id)

        try:
            with io.FileIO(destination_path, "wb") as handle:
                downloader = media_io_base_download(handle, request)
                done = False
                while not done:
                    _status, done = downloader.next_chunk()
        except Exception as exc:
            try:
                destination_path.unlink(missing_ok=True)
            except OSError:
                pass
            if self._is_google_authorization_error(exc):
                self._reset_saved_authorization_after_error(exc)
            raise

        web_view_link = str(metadata.get("webViewLink") or "").strip()
        if not web_view_link:
            web_view_link = self.file_web_view_link(file_id)

        return GoogleDriveDownloadResult(
            file_id=file_id,
            name=file_name,
            local_path=destination_path,
            web_view_link=web_view_link,
        )

    def update_excel(
        self,
        file_id: str,
        file_path: str | Path,
    ) -> GoogleDriveUploadResult:
        return self._update_file(
            file_id,
            file_path,
            mimetype=self.XLSX_MIME_TYPE,
            missing_label="XLSX",
        )

    def _upload_file(
        self,
        file_path: str | Path,
        *,
        mimetype: str,
        missing_label: str,
    ) -> GoogleDriveUploadResult:
        source_path = Path(file_path).expanduser()
        if not source_path.is_file():
            raise FileNotFoundError(f"Файл {missing_label} не найден: {source_path}")

        credentials = self._load_credentials()
        build, media_file_upload, _media_io_base_download = self._load_drive_client_symbols()

        metadata = {"name": source_path.name}
        folder_id = self.folder_id()
        if folder_id:
            metadata["parents"] = [folder_id]

        drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
        media = media_file_upload(
            str(source_path),
            mimetype=mimetype,
            resumable=True,
        )
        uploaded = self._execute_drive_request(
            drive.files().create(
                body=metadata,
                media_body=media,
                fields="id,name,webViewLink",
            ),
            "загрузки файла на Google Drive",
        )

        file_id = str(uploaded.get("id", "") or "").strip()
        if not file_id:
            raise RuntimeError("Google Drive не вернул id загруженного файла")

        self._ensure_anyone_with_link_can_edit(drive, file_id)

        web_view_link = str(uploaded.get("webViewLink", "") or "").strip()
        if not web_view_link:
            web_view_link = f"https://drive.google.com/file/d/{file_id}/view"

        return GoogleDriveUploadResult(
            file_id=file_id,
            name=str(uploaded.get("name", "") or source_path.name),
            web_view_link=web_view_link,
        )

    def _update_file(
        self,
        file_id: str,
        file_path: str | Path,
        *,
        mimetype: str,
        missing_label: str,
    ) -> GoogleDriveUploadResult:
        normalized_file_id = str(file_id or "").strip()
        if not normalized_file_id:
            raise ValueError("Не указан id файла Google Drive для обновления")

        source_path = Path(file_path).expanduser()
        if not source_path.is_file():
            raise FileNotFoundError(f"Файл {missing_label} не найден: {source_path}")

        credentials = self._load_credentials()
        build, media_file_upload, _media_io_base_download = self._load_drive_client_symbols()
        drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
        media = media_file_upload(
            str(source_path),
            mimetype=mimetype,
            resumable=True,
        )
        updated = self._execute_drive_request(
            drive.files().update(
                fileId=normalized_file_id,
                media_body=media,
                fields="id,name,webViewLink",
            ),
            "обновления файла Google Drive",
        )

        updated_file_id = str(updated.get("id", "") or normalized_file_id).strip()
        self._ensure_anyone_with_link_can_edit(drive, updated_file_id)

        web_view_link = str(updated.get("webViewLink", "") or "").strip()
        if not web_view_link:
            web_view_link = f"https://drive.google.com/file/d/{updated_file_id}/view"

        return GoogleDriveUploadResult(
            file_id=updated_file_id,
            name=str(updated.get("name", "") or source_path.name),
            web_view_link=web_view_link,
        )

    def _load_credentials(self):
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
        except ImportError as exc:
            raise RuntimeError(
                "Для загрузки на Google Drive установите зависимости "
                "google-api-python-client, google-auth и google-auth-oauthlib."
            ) from exc

        credentials = None
        token_path = self.token_path()
        if token_path.is_file():
            try:
                credentials = Credentials.from_authorized_user_file(
                    str(token_path),
                    self.SCOPES,
                )
            except (JSONDecodeError, ValueError) as exc:
                self.delete_saved_authorization()
                credentials = None

        if credentials is not None:
            has_scopes = getattr(credentials, "has_scopes", None)
            if callable(has_scopes) and not has_scopes(self.SCOPES):
                self.delete_saved_authorization()
                credentials = None

        if credentials and credentials.valid:
            return credentials

        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
            except Exception:
                self.delete_saved_authorization()
                credentials = None

        if credentials is None or not credentials.valid:
            credentials_path = self.credentials_path()
            if credentials_path is None or not credentials_path.is_file():
                raise RuntimeError(
                    "Сначала выберите OAuth JSON-файл Google Drive в настройках приложения."
                )
            self._validate_client_secrets_file(credentials_path)
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path),
                self.SCOPES,
            )
            try:
                credentials = self._run_local_authorization(flow)
            except Exception as exc:
                self.delete_saved_authorization()
                raise RuntimeError(
                    "Не удалось авторизоваться в Google Drive. "
                    f"{self._authorization_error_hint(exc)} "
                    "Сохраненная авторизация удалена; повторите действие "
                    "и завершите вход в открывшемся браузере."
                ) from exc
        else:
            # Refreshed credentials are valid here.
            pass

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(credentials.to_json(), encoding="utf-8")
        return credentials

    @classmethod
    def _run_local_authorization(cls, flow):
        """Run OAuth on an explicit IPv4 loopback address.

        On Windows ``localhost`` can resolve to ``::1`` while
        google-auth-oauthlib listens on IPv4. Using the literal address for
        both the advertised callback and the listening socket keeps the
        browser redirect on the same interface.
        """
        return flow.run_local_server(
            host=cls.OAUTH_CALLBACK_HOST,
            bind_addr=cls.OAUTH_CALLBACK_HOST,
            port=0,
            timeout_seconds=cls.OAUTH_CALLBACK_TIMEOUT_SECONDS,
            authorization_prompt_message=None,
            success_message=(
                "Авторизация Google Drive завершена. "
                "Можно закрыть эту вкладку и вернуться в приложение."
            ),
            prompt="consent",
        )

    @staticmethod
    def _authorization_error_hint(exc: Exception) -> str:
        text = str(exc).lower()
        winerror = getattr(exc, "winerror", None)

        if "access_denied" in text:
            return "Вход или доступ к Google Drive был отменен."
        if "redirect_uri_mismatch" in text:
            return (
                "Google отклонил адрес возврата OAuth. Выберите JSON клиента "
                "типа Desktop app, а не Web application."
            )
        if "org_internal" in text:
            return (
                "OAuth-клиент доступен только пользователям своей организации Google."
            )
        if "deleted_client" in text or "invalid_client" in text:
            return "OAuth-клиент Google удален, отключен или настроен неверно."
        if "unauthorized_client" in text:
            return (
                "Этот OAuth-клиент не поддерживает вход настольного приложения. "
                "Создайте клиент типа Desktop app."
            )
        if "invalid_grant" in text:
            return (
                "Google отклонил код авторизации. Включите автоматическую "
                "синхронизацию даты и времени Windows и повторите вход."
            )
        if "mismatchingstate" in text or "state mismatch" in text:
            return (
                "Получен ответ от другого или устаревшего окна входа. Закройте "
                "старые вкладки авторизации Google и повторите действие."
            )
        if "timed out" in text or "timeout" in text:
            return (
                "Ответ от браузера не получен за 5 минут. Проверьте, что вход "
                "был завершен и localhost не блокируется антивирусом или фаерволом."
            )
        if winerror == 10048 or "address already in use" in text:
            return "Локальный порт OAuth занят другим приложением."
        if winerror == 10013 or "permission denied" in text:
            return (
                "Windows запретила открыть локальный OAuth-порт. Проверьте "
                "антивирус и правила фаервола для приложения."
            )
        if "connection" in text or "network" in text or "ssl" in text:
            return (
                "Не удалось связаться с сервером Google; проверьте интернет, "
                "прокси и VPN."
            )

        return f"Техническая причина: {type(exc).__name__}."

    @staticmethod
    def _safe_download_name(file_name: str) -> str:
        safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", file_name).strip()
        return safe_name or "google_drive_file.xlsx"

    @staticmethod
    def _is_google_authorization_error(exc: Exception) -> bool:
        status = getattr(getattr(exc, "resp", None), "status", None)
        if status in (401, 403):
            return True

        text = str(exc).lower()
        return any(
            marker in text
            for marker in (
                "invalid_grant",
                "unauthorized",
                "invalid credentials",
                "insufficient authentication scopes",
                "request had insufficient authentication scopes",
            )
        )

    def _reset_saved_authorization_after_error(self, exc: Exception) -> None:
        self.delete_saved_authorization()
        raise RuntimeError(
            "Ошибка авторизации Google Drive. "
            "Сохраненная авторизация google_drive_token.json удалена. "
            "Повторите действие и заново войдите в Google."
        ) from exc

    def _execute_drive_request(self, request: Any, action: str) -> dict[str, Any]:
        try:
            result = request.execute()
        except Exception as exc:
            if self._is_google_authorization_error(exc):
                self._reset_saved_authorization_after_error(exc)
            raise
        return result or {}

    @staticmethod
    def _validate_client_secrets_file(credentials_path: Path) -> None:
        try:
            raw_text = credentials_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise RuntimeError(
                f"Не удалось прочитать OAuth JSON Google Drive: {credentials_path}"
            ) from exc

        if not raw_text.strip():
            raise RuntimeError(
                "Выбранный OAuth JSON Google Drive пустой. "
                "Скачайте client secrets JSON заново и выберите его в настройках."
            )

        try:
            payload = json.loads(raw_text)
        except JSONDecodeError as exc:
            raise RuntimeError(
                "Выбранный OAuth JSON Google Drive не является корректным JSON-файлом."
            ) from exc

        if not isinstance(payload, dict) or "installed" not in payload:
            if isinstance(payload, dict) and "web" in payload:
                raise RuntimeError(
                    "Выбран OAuth JSON типа Web application. В Google Cloud "
                    "создайте OAuth client ID типа Desktop app, скачайте его JSON "
                    "и выберите этот файл в настройках приложения."
                )
            raise RuntimeError(
                "Нужен OAuth client secrets JSON для Desktop app из Google Cloud, "
                "а не другой тип файла."
            )

        installed_config = payload.get("installed")
        required_fields = ("client_id", "client_secret", "auth_uri", "token_uri")
        if not isinstance(installed_config, dict) or any(
            not str(installed_config.get(field, "") or "").strip()
            for field in required_fields
        ):
            raise RuntimeError(
                "OAuth JSON для Desktop app неполный. Скачайте client secrets JSON "
                "заново в Google Cloud и выберите новый файл в настройках."
            )

    @staticmethod
    def _load_drive_client_symbols():
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
        except ImportError as exc:
            raise RuntimeError(
                "Для загрузки на Google Drive установите зависимость "
                "google-api-python-client."
            ) from exc
        return build, MediaFileUpload, MediaIoBaseDownload

    def _ensure_anyone_with_link_can_edit(self, drive: Any, file_id: str) -> None:
        permissions_result = self._execute_drive_request(
            drive.permissions().list(
                fileId=file_id,
                fields="permissions(id,type,role,allowFileDiscovery)",
            ),
            "получения прав доступа Google Drive",
        )
        permissions = permissions_result.get("permissions", [])
        anyone_permission = next(
            (
                permission
                for permission in permissions
                if str(permission.get("type", "")).strip() == "anyone"
            ),
            None,
        )
        permission_body = dict(self.LINK_EDITOR_PERMISSION)
        if anyone_permission:
            permission_body.pop("type", None)
            permission_id = str(anyone_permission.get("id", "") or "").strip()
            if not permission_id:
                raise RuntimeError("Google Drive не вернул id публичного права доступа")
            self._execute_drive_request(
                drive.permissions().update(
                    fileId=file_id,
                    permissionId=permission_id,
                    body=permission_body,
                    fields="id,type,role,allowFileDiscovery",
                ),
                "обновления прав доступа Google Drive",
            )
            return

        self._execute_drive_request(
            drive.permissions().create(
                fileId=file_id,
                body=permission_body,
                fields="id,type,role,allowFileDiscovery",
            ),
            "создания прав доступа Google Drive",
        )
