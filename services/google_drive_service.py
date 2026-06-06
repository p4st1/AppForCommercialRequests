from __future__ import annotations

import json
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path

from config import Config
from utilities.paths import user_path


@dataclass(frozen=True)
class GoogleDriveUploadResult:
    file_id: str
    name: str
    web_view_link: str


class GoogleDriveService:
    SCOPES = ("https://www.googleapis.com/auth/drive.file",)
    DOCX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    XLSX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    TOKEN_FILE_NAME = "google_drive_token.json"

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
    def is_configured(cls) -> bool:
        credentials_path = cls.credentials_path()
        return credentials_path is not None and credentials_path.is_file()

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
        build, media_file_upload = self._load_drive_client_symbols()

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
        uploaded = (
            drive.files()
            .create(
                body=metadata,
                media_body=media,
                fields="id,name,webViewLink",
            )
            .execute()
        )

        file_id = str(uploaded.get("id", "") or "").strip()
        if not file_id:
            raise RuntimeError("Google Drive не вернул id загруженного файла")

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
        build, media_file_upload = self._load_drive_client_symbols()
        drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
        media = media_file_upload(
            str(source_path),
            mimetype=mimetype,
            resumable=True,
        )
        updated = (
            drive.files()
            .update(
                fileId=normalized_file_id,
                media_body=media,
                fields="id,name,webViewLink",
            )
            .execute()
        )

        updated_file_id = str(updated.get("id", "") or normalized_file_id).strip()
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
                raise RuntimeError(
                    "Сохраненная авторизация Google Drive повреждена. "
                    "Удалите файл google_drive_token.json и войдите снова."
                ) from exc

        if credentials and credentials.valid:
            return credentials

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
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
            credentials = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(credentials.to_json(), encoding="utf-8")
        return credentials

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

        if not isinstance(payload, dict) or not any(
            key in payload for key in ("installed", "web")
        ):
            raise RuntimeError(
                "Нужен OAuth client secrets JSON для Desktop app из Google Cloud, "
                "а не другой тип файла."
            )

    @staticmethod
    def _load_drive_client_symbols():
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
        except ImportError as exc:
            raise RuntimeError(
                "Для загрузки на Google Drive установите зависимость "
                "google-api-python-client."
            ) from exc
        return build, MediaFileUpload
