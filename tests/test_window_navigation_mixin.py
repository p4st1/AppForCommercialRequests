import sys
import unittest
from types import ModuleType

from config import Config


class _FakeSignal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)


class _BaseFakeWindow:
    def __init__(self, parent):
        self.parent = parent
        self.shown = False
        self.__class__.instances.append(self)

    def show(self):
        self.shown = True


class _FakeParamsWindow(_BaseFakeWindow):
    instances = []

    def __init__(self, parent):
        super().__init__(parent)
        self.paramsSaved = _FakeSignal()


class _FakeSettingsWindow(_BaseFakeWindow):
    instances = []


class _FakeCustomersWindow(_BaseFakeWindow):
    instances = []


params_module = ModuleType("params")
params_module.mainWindow = _FakeParamsWindow
sys.modules["params"] = params_module

settings_module = ModuleType("settings")
settings_module.mainWindow = _FakeSettingsWindow
sys.modules["settings"] = settings_module

customers_module = ModuleType("customers")
customers_module.mainWindow = _FakeCustomersWindow
sys.modules["customers"] = customers_module

from app.ui.window_navigation_mixin import WindowNavigationMixin


class _FakeMainWindow(WindowNavigationMixin):
    def __init__(self):
        self.calculation_calls = 0
        self.raise_in_calculating = None
        self.error_calls = []

    def calculating(self):
        self.calculation_calls += 1
        if self.raise_in_calculating is not None:
            raise self.raise_in_calculating

    def error(self, title, text):
        self.error_calls.append((title, text))


def _has_bound_callback(callbacks, owner, method_name):
    for callback in callbacks:
        if getattr(callback, "__self__", None) is owner and getattr(
            getattr(callback, "__func__", None),
            "__name__",
            "",
        ) == method_name:
            return True
    return False


class WindowNavigationMixinTests(unittest.TestCase):
    def setUp(self):
        self._old_is_table_opened = Config.isTableOpened
        _FakeParamsWindow.instances.clear()
        _FakeSettingsWindow.instances.clear()
        _FakeCustomersWindow.instances.clear()

    def tearDown(self):
        Config.isTableOpened = self._old_is_table_opened

    def test_open_params_window_connects_recalculate_and_shows(self):
        window = _FakeMainWindow()

        window.openParamsWindow()

        self.assertEqual(len(_FakeParamsWindow.instances), 1)
        created_window = _FakeParamsWindow.instances[0]
        self.assertIs(created_window.parent, window)
        self.assertTrue(created_window.shown)
        self.assertTrue(
            _has_bound_callback(
                created_window.paramsSaved.callbacks,
                window,
                "_recalculate_after_params_save",
            )
        )

    def test_recalculate_after_params_save_skips_when_table_is_closed(self):
        Config.isTableOpened = False
        window = _FakeMainWindow()

        window._recalculate_after_params_save()

        self.assertEqual(window.calculation_calls, 0)
        self.assertEqual(window.error_calls, [])

    def test_recalculate_after_params_save_calls_calculating_when_table_open(self):
        Config.isTableOpened = True
        window = _FakeMainWindow()

        window._recalculate_after_params_save()

        self.assertEqual(window.calculation_calls, 1)
        self.assertEqual(window.error_calls, [])

    def test_recalculate_after_params_save_handles_value_error(self):
        Config.isTableOpened = True
        window = _FakeMainWindow()
        window.raise_in_calculating = ValueError("Bad formula")

        window._recalculate_after_params_save()

        self.assertEqual(window.calculation_calls, 1)
        self.assertEqual(window.error_calls, [("Ошибка", "Bad formula")])

    def test_open_settings_window_shows_window(self):
        window = _FakeMainWindow()

        window.openSettingsWindow()

        self.assertEqual(len(_FakeSettingsWindow.instances), 1)
        created_window = _FakeSettingsWindow.instances[0]
        self.assertIs(created_window.parent, window)
        self.assertTrue(created_window.shown)

    def test_open_suppliers_window_shows_window(self):
        window = _FakeMainWindow()

        window.openSuppliersWindow()

        self.assertEqual(len(_FakeCustomersWindow.instances), 1)
        created_window = _FakeCustomersWindow.instances[0]
        self.assertIs(created_window.parent, window)
        self.assertTrue(created_window.shown)


if __name__ == "__main__":
    unittest.main()
