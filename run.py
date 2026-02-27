from main import mainWindow
from tools import DatabaseTools as Tool
from config import Config
from pathlib import Path
import sys
import os
import traceback



def resourcePath(relativePath):
    return Tool.resourcePath(relativePath)

if __name__ == '__main__':
    try:
        Config.cfg_path = Tool.ensure_user_file(
            'MyApp',
            'utilities/config.json',
            'config.json',
            sync_mode='merge_json_on_source_change',
        )
        Config.db_path = Tool.ensure_user_file('MyApp', 'database/database.db', 'database.db')
        Config.vars_path = Tool.ensure_user_file(
            'MyApp',
            'utilities/variables.json',
            'variables.json',
            sync_mode='merge_json_on_source_change',
        )
        Config.template_path = Tool.ensure_user_file(
            'MyApp',
            'templates/template.xlsx',
            'template.xlsx',
            sync_mode='replace_on_source_change',
        )
        Config.template_docx_path = Tool.ensure_user_file(
            'MyApp',
            'templates/template.docx',
            'template.docx',
            sync_mode='replace_on_source_change',
        )
        Config.template_docx_path_short = Tool.ensure_user_file(
            'MyApp',
            'templates/template_short.docx',
            'template_short.docx',
            sync_mode='replace_on_source_change',
        )
        Config.log_path = Tool.ensure_user_file('MyApp', 'templates/logs.log', 'logs.log')
        Config.logo_path = Tool.ensure_user_file(
            'MyApp',
            'assets/app.jpg',
            'app.jpg',
            sync_mode='replace_on_source_change',
        )
        Config.print_path = Tool.ensure_user_file(
            'MyApp',
            'assets/print.png',
            'print.png',
            sync_mode='replace_on_source_change',
        )
        Config.sign_path = Tool.ensure_user_file(
            'MyApp',
            'assets/sign.png',
            'sign.png',
            sync_mode='replace_on_source_change',
        )

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
        Tool.write_log("🚀 APPLICATION STARTING")
        Tool.write_log(f"Current working directory: {os.getcwd()}")
        Tool.write_log(f"Executable path: {sys.executable}")
        Tool.write_log(f"Python path: {sys.prefix}")
        Tool.write_log(f"argv[0]: {sys.argv[0]}")
        Tool.write_log(f"frozen: {getattr(sys, 'frozen', False)}")
        Tool.write_log(f"MEIPASS: {getattr(sys, '_MEIPASS', 'NOT SET')}")
        Tool.write_log("Environment variables:")
        for key in ['PATH', 'PYTHONPATH', 'HOME', 'USER']:
            value = os.environ.get(key, 'NOT SET')
            Tool.write_log(f"  {key}: {value}")
        Tool.write_log("=== ДИАГНОСТИКА ===")
        Tool.write_log(f"Текущая папка: {os.getcwd()}")
        Tool.write_log(f"MEIPASS: {getattr(sys, '_MEIPASS', 'NOT SET')}")
        test_path = resourcePath("ui/mainGui.ui")
        Tool.write_log(f"Ожидаемый путь: {test_path}")
        Tool.write_log(f"Файл существует: {os.path.exists(test_path)}")
        ui_dir = resourcePath("ui")
        if os.path.exists(ui_dir):
            Tool.write_log(f"Содержимое папки ui: {os.listdir(ui_dir)}")
        else:
            Tool.write_log("Папка ui не найдена!")
        ui_dir = resourcePath("utilities")
        if os.path.exists(ui_dir):
            Tool.write_log(f"Содержимое папки utilities: {os.listdir(ui_dir)}")
        else:
            Tool.write_log("Папка utilities не найдена!")
        Tool.write_log("Testing imports...")
        try:
            from PySide6.QtWidgets import QApplication, QMainWindow
            Tool.write_log("✅ PySide6 import successful")
        except ImportError as e:
            Tool.log_exception("PySide6 import failed", e, include_traceback=False)
        Tool.write_log("Creating QApplication...")
        app = QApplication(sys.argv)
        ex = mainWindow()
        ex.show()
        sys.exit(app.exec())

    except Exception as e:
        Tool.log_exception("Критическая ошибка запуска приложения", e, include_traceback=True)
        error_details = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        error_file = Path.home() / 'myapp_error.txt'
        error_file.write_text(f"Error: {e}\n\n{error_details}")


