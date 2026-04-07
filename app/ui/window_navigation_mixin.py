from config import Config
from customers import mainWindow as customersWindow
from params import mainWindow as paramsWindow
from settings import mainWindow as settingsWindow


class WindowNavigationMixin:
    def openParamsWindow(self):
        window = paramsWindow(self)
        window.paramsSaved.connect(self._recalculate_after_params_save)
        window.show()

    def _recalculate_after_params_save(self):
        if not Config.isTableOpened:
            return
        try:
            self.calculating()
        except ValueError as e:
            self.error("Ошибка", str(e))

    def openSettingsWindow(self):
        window = settingsWindow(self)
        window.show()

    def openSuppliersWindow(self):
        window = customersWindow(self)
        window.show()
