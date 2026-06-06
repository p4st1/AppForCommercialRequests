from pathlib import Path
import os
import sys
import tempfile
import traceback

from config import Config
from tools import DatabaseTools as Tool
from version_check import check_release_version


APP_NAME = "MyApp"


def resourcePath(relativePath):
    return Tool.resourcePath(relativePath)


def _configure_log_path(user_dir: Path) -> None:
    log_path = user_dir / "logs" / "logs.log"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.touch(exist_ok=True)
        Config.log_path = log_path
    except OSError:
        fallback = Path(tempfile.gettempdir()) / APP_NAME / "logs" / "logs.log"
        fallback.parent.mkdir(parents=True, exist_ok=True)
        fallback.touch(exist_ok=True)
        Config.log_path = fallback


def _write_startup_error(error: Exception) -> None:
    error_details = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    candidates = []
    configured_log_path = str(getattr(Config, "log_path", "") or "").strip()
    if configured_log_path:
        candidates.append(Path(configured_log_path).parent / "startup_error.txt")
    candidates.append(Path(tempfile.gettempdir()) / APP_NAME / "logs" / "startup_error.txt")

    for error_file in candidates:
        try:
            error_file.parent.mkdir(parents=True, exist_ok=True)
            error_file.write_text(f"Error: {error}\n\n{error_details}", encoding="utf-8")
            return
        except OSError:
            continue
    sys.stderr.write(f"Error: {error}\n\n{error_details}")


def _configure_user_files() -> Path:
    user_dir = Tool.user_data_dir(APP_NAME)
    _configure_log_path(user_dir)

    migrated = Tool.migrate_legacy_user_files(APP_NAME)
    for target_name, source_path in migrated.items():
        Tool.write_log(f"Мигрирован legacy-файл: {source_path} -> {user_dir / target_name}")

    Config.cfg_path = Tool.ensure_user_file(
        APP_NAME,
        'utilities/config.json',
        'config.json',
        sync_mode='merge_json_on_source_change',
    )
    Config.db_path = Tool.ensure_user_file(
        APP_NAME,
        'database/database.db',
        'database/database.db',
    )
    Config.vars_path = Tool.ensure_user_file(
        APP_NAME,
        'utilities/variables.json',
        'variables.json',
        sync_mode='merge_json_on_source_change',
    )
    return user_dir


def _configure_resource_paths() -> Path:
    resources_dir = Tool.app_dir()
    Config.template_path = resources_dir / 'templates' / 'template.xlsx'
    Config.template_docx_path = resources_dir / 'templates' / 'template.docx'
    Config.template_docx_path_short = resources_dir / 'templates' / 'template_short.docx'
    Config.logo_path = resources_dir / 'assets' / 'app.jpg'
    Config.print_path = resources_dir / 'assets' / 'print.png'
    Config.sign_path = resources_dir / 'assets' / 'sign.png'

    bundled_playwright_browsers = resources_dir / "playwright" / "driver" / "package" / ".local-browsers"
    if bundled_playwright_browsers.exists():
        os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(bundled_playwright_browsers))
        Tool.write_log(f"Bundled Playwright browsers: {bundled_playwright_browsers}")
    return resources_dir


def _load_config() -> None:
    try:
        current = Tool.load_json(Config.cfg_path)
    except Exception as e:
        Tool.log_exception(
            f"Не удалось загрузить конфиг: {Config.cfg_path}",
            e,
            include_traceback=False,
        )
        current = {}
    normalized = Tool.merge_config_with_defaults(current)
    Tool.save_json_atomic(Config.cfg_path, normalized)
    Config.config = normalized["config"]
    Config.settings = normalized["settings"]


def _write_startup_diagnostics(user_dir: Path) -> None:
    Tool.write_log("=" * 50)
    Tool.write_log("APPLICATION STARTING")
    Tool.write_log(f"App resources directory: {Tool.app_dir()}")
    Tool.write_log(f"User data directory: {user_dir}")
    Tool.write_log(f"Executable path: {sys.executable}")
    Tool.write_log(f"Python path: {sys.prefix}")
    Tool.write_log(f"argv[0]: {sys.argv[0]}")
    Tool.write_log(f"frozen: {getattr(sys, 'frozen', False)}")
    Tool.write_log("Environment variables:")
    for key in ['PATH', 'PYTHONPATH', 'HOME', 'USER', 'PLAYWRIGHT_BROWSERS_PATH']:
        value = os.environ.get(key, 'NOT SET')
        Tool.write_log(f"  {key}: {value}")
    Tool.write_log("=== PATH DIAGNOSTICS ===")
    test_path = resourcePath("ui/mainGui.ui")
    Tool.write_log(f"Ожидаемый путь: {test_path}")
    Tool.write_log(f"Файл существует: {Path(test_path).exists()}")
    ui_dir = resourcePath("ui")
    if Path(ui_dir).exists():
        Tool.write_log(f"Содержимое папки ui: {[path.name for path in Path(ui_dir).iterdir()]}")
    else:
        Tool.write_log("Папка ui не найдена!")
    utilities_dir = resourcePath("utilities")
    if Path(utilities_dir).exists():
        Tool.write_log(
            f"Содержимое папки utilities: {[path.name for path in Path(utilities_dir).iterdir()]}"
        )
    else:
        Tool.write_log("Папка utilities не найдена!")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    smoke_test = "--smoke-test" in argv

    try:
        user_dir = _configure_user_files()
        resources_dir = _configure_resource_paths()
        _load_config()
        _write_startup_diagnostics(user_dir)

        Tool.write_log("Testing imports...")
        from main import mainWindow
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication, QMessageBox

        Tool.write_log("PySide6 import successful")
        if smoke_test:
            missing = [
                str(path)
                for path in (
                    resources_dir / 'templates' / 'template.xlsx',
                    resources_dir / 'templates' / 'template.docx',
                    resources_dir / 'assets' / 'app.jpg',
                    resources_dir / 'assets' / 'updates.txt',
                )
                if not path.exists()
            ]
            if missing:
                raise RuntimeError("Missing bundled resources: " + ", ".join(missing))
            Tool.write_log("Smoke test successful")
            return 0

        version_check_result = check_release_version(resourcePath, timeout_seconds=2.5)
        Tool.write_log(
            "Version check status: "
            f"{version_check_result.status} "
            f"(local={version_check_result.local_version or 'n/a'}, "
            f"release={version_check_result.remote_version or 'n/a'})"
        )
        if version_check_result.details:
            Tool.write_log(f"Version check details: {version_check_result.details}")

        Tool.write_log("Creating QApplication...")
        app = QApplication(argv)
        ex = mainWindow()
        ex.show()

        if version_check_result.status == "outdated":
            def show_update_message():
                QMessageBox.warning(
                    ex,
                    "Версия устарела",
                    (
                        "У вас установлена устаревшая версия приложения.\n\n"
                        f"Текущая версия: {version_check_result.local_version}\n"
                        f"Актуальная версия release: {version_check_result.remote_version}\n\n"
                        f"Скачать обновление: {version_check_result.release_url}"
                    ),
                )

            QTimer.singleShot(0, show_update_message)

        return int(app.exec())

    except Exception as e:
        Tool.log_exception("Критическая ошибка запуска приложения", e, include_traceback=True)
        _write_startup_error(e)
        return 1


if __name__ == '__main__':
    sys.exit(main())
