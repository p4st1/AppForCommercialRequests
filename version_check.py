import json
import re
import ssl
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

try:
    import certifi
except Exception:
    certifi = None

VERSION_CHECK_HEADERS = {
    "User-Agent": "AppForCommercialRequests-Version-Check",
    "Accept": "application/vnd.github+json",
}


@dataclass(frozen=True)
class VersionMeta:
    version: str
    repo: str
    release_branch: str
    release_url: str


@dataclass(frozen=True)
class VersionCheckResult:
    status: str
    local_version: str
    remote_version: str
    release_url: str
    details: str


def _latest_release_api_url(repo: str) -> str:
    return f"https://api.github.com/repos/{repo}/releases/latest"


def _remote_version_json_url(meta: VersionMeta) -> str:
    return (
        "https://raw.githubusercontent.com/"
        f"{meta.repo}/{meta.release_branch}/utilities/version.json"
    )


def _remote_version_json_urls(meta: VersionMeta) -> list[str]:
    return [
        _remote_version_json_url(meta),
        f"https://raw.githubusercontent.com/{meta.repo}/{meta.release_branch}/version.json",
        f"https://github.com/{meta.repo}/releases/latest/download/version.json",
    ]


def _safe_text(value: object, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def load_local_version_meta(resource_path: Callable[[str], str]) -> VersionMeta:
    version_path = Path(resource_path("utilities/version.json"))
    with open(version_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError("utilities/version.json должен содержать JSON-объект")

    repo = _safe_text(raw.get("repo"), "p4st1/AppForCommercialRequests")
    release_branch = _safe_text(raw.get("release_branch"), "release")
    release_url = _safe_text(
        raw.get("release_url"),
        f"https://github.com/{repo}/releases/latest",
    )

    return VersionMeta(
        version=_safe_text(raw.get("version")),
        repo=repo,
        release_branch=release_branch,
        release_url=release_url,
    )


def trusted_ssl_context() -> ssl.SSLContext:
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return ssl.create_default_context()


def _fetch_json(url: str, timeout_seconds: float) -> object:
    request = Request(url, headers=VERSION_CHECK_HEADERS)
    with urlopen(request, timeout=timeout_seconds, context=trusted_ssl_context()) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def _extract_release_version(raw: object) -> str:
    if not isinstance(raw, dict):
        raise ValueError("Metadata latest release должен быть JSON-объектом")

    for field_name in ("tag_name", "name"):
        candidate = _safe_text(raw.get(field_name))
        if not candidate:
            continue
        match = re.search(r"v?\d+(?:\.\d+)*(?:[-+][0-9A-Za-z.-]+)?", candidate)
        if match:
            return match.group(0)

    raise ValueError("В metadata latest release отсутствует tag_name/name с версией")


def _fetch_github_latest_release_version(
    meta: VersionMeta,
    timeout_seconds: float,
) -> str:
    raw = _fetch_json(_latest_release_api_url(meta.repo), timeout_seconds)
    return _extract_release_version(raw)


def _fetch_remote_version_json_version(
    meta: VersionMeta,
    timeout_seconds: float,
) -> str:
    errors = []
    for url in _remote_version_json_urls(meta):
        try:
            raw = _fetch_json(url, timeout_seconds)
            if not isinstance(raw, dict):
                raise ValueError("Удаленный version.json должен содержать JSON-объект")
            remote_version = _safe_text(raw.get("version"))
            if not remote_version:
                raise ValueError("В удаленном version.json отсутствует поле version")
            return remote_version
        except Exception as error:
            errors.append(f"{url}: {error}")

    raise URLError("; ".join(errors))


def fetch_release_version(meta: VersionMeta, timeout_seconds: float = 2.5) -> str:
    try:
        return _fetch_github_latest_release_version(meta, timeout_seconds)
    except (HTTPError, URLError, TimeoutError, ValueError) as release_error:
        try:
            return _fetch_remote_version_json_version(meta, timeout_seconds)
        except (HTTPError, URLError, TimeoutError) as version_json_error:
            raise URLError(
                "latest release metadata: "
                f"{release_error}; remote version.json: {version_json_error}"
            ) from version_json_error
        except Exception as version_json_error:
            raise ValueError(
                "latest release metadata: "
                f"{release_error}; remote version.json: {version_json_error}"
            ) from version_json_error


def _parse_semver(version_text: str) -> tuple[int, ...]:
    # Поддерживаем v2.0.0, 2.0.0, 2.0.0-rc1, 2.0.0+build.
    match = re.match(r"^\s*v?(\d+(?:\.\d+)*)(?:[-+].*)?\s*$", version_text or "")
    if not match:
        raise ValueError(f"Неверный формат версии: {version_text}")
    return tuple(int(part) for part in match.group(1).split("."))


def compare_versions(local_version: str, remote_version: str) -> int:
    local = _parse_semver(local_version)
    remote = _parse_semver(remote_version)
    if local < remote:
        return -1
    if local > remote:
        return 1
    return 0


def check_release_version(
    resource_path: Callable[[str], str],
    timeout_seconds: float = 2.5,
) -> VersionCheckResult:
    try:
        local_meta = load_local_version_meta(resource_path)
    except Exception as error:
        return VersionCheckResult(
            status="unknown",
            local_version="",
            remote_version="",
            release_url="",
            details=f"Не удалось прочитать локальную версию: {error}",
        )

    local_version = _safe_text(local_meta.version)
    if not local_version:
        return VersionCheckResult(
            status="unknown",
            local_version="",
            remote_version="",
            release_url=local_meta.release_url,
            details="В локальном version.json отсутствует поле version",
        )

    try:
        remote_version = fetch_release_version(local_meta, timeout_seconds=timeout_seconds)
    except (HTTPError, URLError, TimeoutError) as error:
        return VersionCheckResult(
            status="unknown",
            local_version=local_version,
            remote_version="",
            release_url=local_meta.release_url,
            details=f"Не удалось получить версию release: {error}",
        )
    except Exception as error:
        return VersionCheckResult(
            status="unknown",
            local_version=local_version,
            remote_version="",
            release_url=local_meta.release_url,
            details=f"Ошибка обработки версии release: {error}",
        )

    try:
        comparison = compare_versions(local_version, remote_version)
    except ValueError as error:
        return VersionCheckResult(
            status="unknown",
            local_version=local_version,
            remote_version=remote_version,
            release_url=local_meta.release_url,
            details=f"Некорректный формат версии: {error}",
        )

    if comparison < 0:
        return VersionCheckResult(
            status="outdated",
            local_version=local_version,
            remote_version=remote_version,
            release_url=local_meta.release_url,
            details="Установлена устаревшая версия",
        )
    if comparison > 0:
        return VersionCheckResult(
            status="ahead",
            local_version=local_version,
            remote_version=remote_version,
            release_url=local_meta.release_url,
            details="Локальная версия новее release",
        )
    return VersionCheckResult(
        status="up_to_date",
        local_version=local_version,
        remote_version=remote_version,
        release_url=local_meta.release_url,
        details="Версия актуальна",
    )
