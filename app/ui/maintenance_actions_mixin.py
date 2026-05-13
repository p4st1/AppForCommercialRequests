import shutil

from PySide6.QtWidgets import QMessageBox

from config import Config
from tools import DatabaseTools as Tool


class MaintenanceActionsMixin:
    def testFeature(self, checked):
        QMessageBox.about(
            self,
            "ВНИМАНИЕ",
            "Для включения тестовой функции, необходимо перезапустить приложение"
            "<br>*Возможны неточности в склонении слов</br>",
        )

        Config.settings["testFeature"] = checked
        self.saveConfig()

    def clear_cache(self):
        dst = Tool.user_config_path()
        dst.parent.mkdir(parents=True, exist_ok=True)
        src = Tool.resourcePath("utilities/config.json")
        shutil.copy2(src, dst)

        self.loadConfig()
        self.ensureOutputDirs()
        if Config.settings["autoFill"]:
            self.ui.logisticNum.setText(Config.config["logisticNum"])
            self.ui.customLine.setText(Config.config["customNum"])
            self.ui.termDeliveryLine.setText(Config.config["termDelivery"])
            self.ui.markupLine.setText(Config.config["markup"])
            self.ui.requestNumberLine.setText(Config.config.get("requestNumber", ""))
            self.ui.logisticVar.setCurrentIndex(int(Config.config["logisticVar"]))
        self.processFormula()
