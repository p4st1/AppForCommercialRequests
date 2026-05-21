from __future__ import annotations

import os
import shutil
import sys
import tempfile
from functools import lru_cache
from pathlib import Path


APP_NAME = "MyApp"


def _is_packaged() -> bool:
    return bool(getattr(sys, "frozen", False) or "__compiled__" in globals())


def app_dir() -> Path:
    """Return the directory that contains bundled read-only application files."""
    override = os.environ.get("MYAPP_APP_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()

    current_file = Path(__file__).resolve()
    project_root = current_file.parents[1]
    if _looks_like_app_root(project_root):
        return project_root

    for candidate in _app_root_candidates():
        if _looks_like_app_root(candidate):
            return candidate

    return project_root


@lru_cache(maxsize=None)
def user_data_dir(app_name: str = APP_NAME) -> Path:
    """Return and create the per-user writable data directory."""
    app_name = str(app_name or APP_NAME).strip() or APP_NAME
    override = os.environ.get("MYAPP_USER_DATA_DIR", "").strip()
    if override:
        return _ensure_writable_dir(Path(override).expanduser(), app_name)

    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA")
        base_dir = Path(base) if base else Path.home() / "AppData" / "Roaming"
    elif sys.platform == "darwin":
        base_dir = Path.home() / "Library" / "Application Support"
    else:
        base_dir = Path.home() / ".local" / "share"

    target = (base_dir / app_name).expanduser()
    return _ensure_writable_dir(target, app_name)


def _ensure_writable_dir(target: Path, app_name: str = APP_NAME) -> Path:
    try:
        target.mkdir(parents=True, exist_ok=True)
        probe = target / ".write_test"
        probe.write_text("", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return target
    except OSError:
        fallback = Path(tempfile.gettempdir()) / app_name
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def bundled_path(*parts: str | os.PathLike[str]) -> Path:
    path = Path(*parts)
    if path.is_absolute():
        return path
    return app_dir() / path


def user_path(*parts: str | os.PathLike[str], app_name: str = APP_NAME) -> Path:
    return user_data_dir(app_name) / Path(*parts)


def user_subdir(*parts: str | os.PathLike[str], app_name: str = APP_NAME) -> Path:
    directory = user_path(*parts, app_name=app_name)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def legacy_user_file_candidates(
    target_name: str | os.PathLike[str],
    *,
    bundled_rel_path: str | os.PathLike[str] | None = None,
) -> list[Path]:
    """Return old user-writable locations used before the user data directory."""
    target_path = Path(target_name)
    names: list[Path] = [target_path]

    if target_path.parent != Path("."):
        names.append(Path(target_path.name))
    if target_path.name == "database.db":
        names.append(Path("database") / "database.db")
    if bundled_rel_path is not None:
        names.append(Path(bundled_rel_path))

    unique_names: list[Path] = []
    for name in names:
        if name not in unique_names:
            unique_names.append(name)

    candidates: list[Path] = []
    for base in _legacy_base_dirs():
        for name in unique_names:
            candidate = base / name
            if candidate not in candidates:
                candidates.append(candidate)
    return candidates


def migrate_legacy_user_files(
    migrations: dict[str, tuple[str, ...]],
    *,
    app_name: str = APP_NAME,
) -> dict[str, Path]:
    """Copy old writable files from app/exe locations into user_data_dir().

    Existing files in the new location are never overwritten.
    """
    migrated: dict[str, Path] = {}
    root = user_data_dir(app_name)

    for target_name, legacy_names in migrations.items():
        target = root / target_name
        if target.exists():
            continue

        target_parent = target.parent
        target_parent.mkdir(parents=True, exist_ok=True)

        for legacy_name in legacy_names:
            for source in legacy_user_file_candidates(legacy_name):
                if not source.exists() or not source.is_file():
                    continue
                try:
                    if source.resolve() == target.resolve():
                        continue
                except OSError:
                    pass
                try:
                    shutil.copy2(source, target)
                except OSError:
                    continue
                migrated[target_name] = source
                break
            if target.exists():
                break

    return migrated


def _looks_like_app_root(path: Path) -> bool:
    markers = ("assets", "templates", "utilities")
    return any((path / marker).exists() for marker in markers)


def _app_root_candidates() -> list[Path]:
    candidates: list[Path] = []
    for raw in (sys.argv[0] if sys.argv else "", sys.executable):
        if not raw:
            continue
        try:
            candidates.append(Path(raw).resolve().parent)
        except OSError:
            continue
    return _dedupe_paths(candidates)


def _legacy_base_dirs() -> list[Path]:
    candidates = [app_dir()]

    if _is_packaged():
        for raw in (sys.argv[0] if sys.argv else "", sys.executable):
            if not raw:
                continue
            try:
                candidates.append(Path(raw).resolve().parent)
            except OSError:
                continue

    return _dedupe_paths(candidates)


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        try:
            key = str(path.resolve())
        except OSError:
            key = str(path)
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result
