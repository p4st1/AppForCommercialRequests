from main import mainWindow
from tools import DatabaseTools as Tool
from config import Config
from pathlib import Path
import sys
import os



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
        Config.template_path = Tool.ensure_user_file('MyApp', 'templates/template.xlsx', 'template.xlsx')
        Config.log_path = Tool.ensure_user_file('MyApp', 'templates/logs.log', 'logs.log')
        Config.logo_path = Tool.ensure_user_file('MyApp', 'assets/app.jpg', 'app.jpg')
        
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
            Tool.write_log(f"❌ PySide6 import failed: {e}")
        Tool.write_log("Creating QApplication...")
        app = QApplication(sys.argv)
        ex = mainWindow()
        ex.show()
        sys.exit(app.exec())
        
        Tool.write_log("✅ QApplication created")      
        Tool.write_log("✅ Window shown - application running")
        
        success_file = Path.home() / 'myapp_success.txt'
        success_file.write_text("Application started successfully!")
        
        Tool.write_log(f"{Tools.resourcePath(Config.config['pathToSaveCP'])}")
    
        app.exec_()
        
    except Exception as e:
        Tool.write_log(f"💥 CRITICAL ERROR: {e}")
        import traceback
        error_details = traceback.format_exc()
        Tool.write_log(f"Traceback:\n{error_details}")
        error_file = Path.home() / 'myapp_error.txt'
        error_file.write_text(f"Error: {e}\n\n{error_details}")

    