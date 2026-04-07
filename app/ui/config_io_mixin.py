from pathlib import Path

from config import Config
from tools import DatabaseTools as Tool


class ConfigIoMixin:
    def loadConfig(self):
        try:
            data = Tool.load_json(Config.cfg_path)
        except Exception as e:
            Tool.log_exception(
                f"Не удалось загрузить конфигурацию: {Config.cfg_path}",
                e,
                include_traceback=False,
            )
            data = {}
        normalized = Tool.merge_config_with_defaults(data)
        Config.config = normalized["config"]
        Config.settings = normalized["settings"]
        self.saveConfig()

    def saveConfig(self):
        Tool.save_json_atomic(
            Config.cfg_path,
            {"config": Config.config, "settings": Config.settings},
        )

    def ensureOutputDirs(self):
        default_dir = Path.home() / "Documents"
        cp_dir = Tool.ensure_directory(Config.config.get("pathToSaveCP"), default_dir)
        excel_dir = Tool.ensure_directory(Config.config.get("pathToSaveExcel") or cp_dir, cp_dir)
        Config.config["pathToSaveCP"] = str(cp_dir)
        Config.config["pathToSaveExcel"] = str(excel_dir)
