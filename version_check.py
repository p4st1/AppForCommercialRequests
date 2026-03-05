import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen


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
        f"https://github.com/{repo}/releases",
    )

    return VersionMeta(
        version=_safe_text(raw.get("version")),
        repo=repo,
        release_branch=release_branch,
        release_url=release_url,
    )


def fetch_release_version(meta: VersionMeta, timeout_seconds: float = 2.5) -> str:
    url = (
        "https://raw.githubusercontent.com/"
        f"{meta.repo}/{meta.release_branch}/utilities/version.json"
    )
    request = Request(url, headers={"User-Agent": "MyApp-Version-Check"})
    with urlopen(request, timeout=timeout_seconds) as response:
        payload = response.read().decode("utf-8")

    raw = json.loads(payload)
    if not isinstance(raw, dict):
        raise ValueError("Удаленный version.json должен содержать JSON-объект")
    remote_version = _safe_text(raw.get("version"))
    if not remote_version:
        raise ValueError("В удаленном version.json отсутствует поле version")
    return remote_version


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
