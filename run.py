from main import mainWindow
from tools import DatabaseTools as Tool
from config import Config
from pathlib import Path
import time
import sys
import os

def write_log(message):
    log_path = Path.home() / 'myapp_startup.log'
    with open(log_path, 'a', encoding='utf-8') as f:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {message}\n")

def resourcePath(relativePath):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relativePath)
    
if __name__ == '__main__':
    try:
        Config.cfg_path = Tool.ensure_user_file('MyApp', 'utilities/config.json', 'config.json')
        Config.db_path = Tool.ensure_user_file('MyApp', 'database/database.db', 'database.db')
        Config.vars_path = Tool.ensure_user_file('MyApp', 'utilities/variables.json', 'variables.json')
        print('cfg path: ', Config.cfg_path)
        print('db path: ', Config.db_path)
        print('vars path: ', Config.vars_path)
        write_log("=" * 50)
        write_log("🚀 APPLICATION STARTING")
        write_log(f"Current working directory: {os.getcwd()}")
        write_log(f"Executable path: {sys.executable}")
        write_log(f"Python path: {sys.prefix}")
        write_log(f"argv[0]: {sys.argv[0]}")
        write_log(f"frozen: {getattr(sys, 'frozen', False)}")
        write_log(f"MEIPASS: {getattr(sys, '_MEIPASS', 'NOT SET')}")
        write_log("Environment variables:")
        for key in ['PATH', 'PYTHONPATH', 'HOME', 'USER']:
            value = os.environ.get(key, 'NOT SET')
            write_log(f"  {key}: {value}")
        write_log("=== ДИАГНОСТИКА ===")
        write_log(f"Текущая папка: {os.getcwd()}")
        write_log(f"MEIPASS: {getattr(sys, '_MEIPASS', 'NOT SET')}")
        test_path = resourcePath("ui/mainGui.ui")
        write_log(f"Ожидаемый путь: {test_path}")
        write_log(f"Файл существует: {os.path.exists(test_path)}")
        ui_dir = resourcePath("ui")
        if os.path.exists(ui_dir):
            write_log(f"Содержимое папки ui: {os.listdir(ui_dir)}")
        else:
            write_log("Папка ui не найдена!")
        ui_dir = resourcePath("utilities")
        if os.path.exists(ui_dir):
            write_log(f"Содержимое папки utilities: {os.listdir(ui_dir)}")
        else:
            write_log("Папка utilities не найдена!")
        write_log("Testing imports...")
        try:
            from PySide6.QtWidgets import QApplication, QMainWindow
            write_log("✅ PySide6 import successful")
        except ImportError as e:
            write_log(f"❌ PySide6 import failed: {e}")
        write_log("Creating QApplication...")
        app = QApplication(sys.argv)
        ex = mainWindow()
        ex.show()
        sys.exit(app.exec())
        write_log("✅ QApplication created")      
        write_log("✅ Window shown - application running")
        success_file = Path.home() / 'myapp_success.txt'
        success_file.write_text("Application started successfully!")
    
        app.exec_()
        
    except Exception as e:
        write_log(f"💥 CRITICAL ERROR: {e}")
        import traceback
        error_details = traceback.format_exc()
        write_log(f"Traceback:\n{error_details}")
        error_file = Path.home() / 'myapp_error.txt'
        error_file.write_text(f"Error: {e}\n\n{error_details}")

    