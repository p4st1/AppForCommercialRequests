from main import mainWindow
from tools import DatabaseTools as Tool
from config import Config
from version_check import check_release_version
from pathlib import Path
import sys
import os
import traceback


APP_NAME = "MyApp"


def resourcePath(relativePath):
    return Tool.resourcePath(relativePath)

if __name__ == '__main__':
    try:
        user_dir = Tool.user_data_dir(APP_NAME)
        Config.log_path = user_dir / "logs" / "logs.log"
        Config.log_path.parent.mkdir(parents=True, exist_ok=True)
        Config.log_path.touch(exist_ok=True)

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
        resources_dir = Tool.app_dir()
        Config.template_path = resources_dir / 'templates' / 'template.xlsx'
        Config.template_docx_path = resources_dir / 'templates' / 'template.docx'
        Config.template_docx_path_short = resources_dir / 'templates' / 'template_short.docx'
        Config.logo_path = resources_dir / 'assets' / 'app.jpg'
        Config.print_path = resources_dir / 'assets' / 'print.png'
        Config.sign_path = resources_dir / 'assets' / 'sign.png'

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

        Tool.write_log("=" * 50)
        Tool.write_log("APPLICATION STARTING")
        Tool.write_log(f"App resources directory: {Tool.app_dir()}")
        Tool.write_log(f"User data directory: {user_dir}")
        Tool.write_log(f"Executable path: {sys.executable}")
        Tool.write_log(f"Python path: {sys.prefix}")
        Tool.write_log(f"argv[0]: {sys.argv[0]}")
        Tool.write_log(f"frozen: {getattr(sys, 'frozen', False)}")
        bundled_playwright_browsers = resources_dir / "playwright" / "driver" / "package" / ".local-browsers"
        if bundled_playwright_browsers.exists():
            os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(bundled_playwright_browsers))
            Tool.write_log(f"Bundled Playwright browsers: {bundled_playwright_browsers}")
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
        ui_dir = resourcePath("utilities")
        if Path(ui_dir).exists():
            Tool.write_log(
                f"Содержимое папки utilities: {[path.name for path in Path(ui_dir).iterdir()]}"
            )
        else:
            Tool.write_log("Папка utilities не найдена!")
        Tool.write_log("Testing imports...")
        try:
            from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
            from PySide6.QtCore import QTimer
            Tool.write_log("✅ PySide6 import successful")
        except ImportError as e:
            Tool.log_exception("PySide6 import failed", e, include_traceback=False)

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
        app = QApplication(sys.argv)
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

        sys.exit(app.exec())

    except Exception as e:
        Tool.log_exception("Критическая ошибка запуска приложения", e, include_traceback=True)
        error_details = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        error_file = Tool.user_data_dir(APP_NAME) / "logs" / "startup_error.txt"
        error_file.parent.mkdir(parents=True, exist_ok=True)
        error_file.write_text(f"Error: {e}\n\n{error_details}")
