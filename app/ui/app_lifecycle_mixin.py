from config import Config
from tools import DatabaseTools as Tool


class AppLifecycleMixin:
    def resourcePath(self, relativePath):
        return Tool.resourcePath(relativePath)

    def closeEvent(self, event):
        Config.config["logisticNum"] = self.ui.logisticNum.text()
        Config.config["customNum"] = self.ui.customLine.text()
        Config.config["termDelivery"] = self.ui.termDeliveryLine.text()
        Config.config["markup"] = self.ui.markupLine.text()
        Config.config["requestNumber"] = self.ui.requestNumberLine.text().strip()
        Config.config["logisticVar"] = str(self.ui.logisticVar.currentIndex())
        self.ensureOutputDirs()
        self.saveConfig()
        self.db.close()
        super().closeEvent(event)

    def funcExitSystem(self):
        self.close()
