from typing import Any

from config import Config
from tools import DatabaseTools as Tool


class AppLifecycleMixin:
    BACKGROUND_WORKER_STOP_TIMEOUT_MS = 7000
    BACKGROUND_WORKER_TERMINATE_TIMEOUT_MS = 1500
    BACKGROUND_WORKER_ATTRS = (
        "_site_status_worker",
        "_auth_status_worker",
        "_auth_login_worker",
        "_load_trades_worker",
        "_load_retrades_worker",
        "_export_trade_worker",
        "_retrade_import_worker",
        "_submission_submit_worker",
    )
    BACKGROUND_WORKER_DICT_ATTRS = (
        "_excel_preview_workers",
    )

    def resourcePath(self, relativePath):
        return Tool.resourcePath(relativePath)

    @staticmethod
    def _is_worker_running(worker: Any) -> bool:
        is_running = getattr(worker, "isRunning", None)
        if not callable(is_running):
            return False
        try:
            return bool(is_running())
        except RuntimeError:
            return False

    @staticmethod
    def _call_worker_method(worker: Any, method_name: str, *args: Any) -> Any:
        method = getattr(worker, method_name, None)
        if not callable(method):
            return None
        return method(*args)

    def _stop_qthread_worker_instance(self, worker: Any, label: str) -> bool:
        if worker is None:
            return True

        if self._is_worker_running(worker):
            try:
                self._call_worker_method(worker, "requestInterruption")
                self._call_worker_method(worker, "quit")
            except Exception as exc:
                Tool.write_log(f"Failed to request worker stop ({label}): {exc}")

            stopped = False
            wait = getattr(worker, "wait", None)
            if callable(wait):
                try:
                    stopped = bool(wait(self.BACKGROUND_WORKER_STOP_TIMEOUT_MS))
                except TypeError:
                    stopped = bool(wait())
                except Exception as exc:
                    Tool.write_log(f"Failed to wait worker stop ({label}): {exc}")

            if not stopped and self._is_worker_running(worker):
                Tool.write_log(f"Worker did not stop in time, terminating: {label}")
                try:
                    self._call_worker_method(worker, "terminate")
                    if callable(wait):
                        wait(self.BACKGROUND_WORKER_TERMINATE_TIMEOUT_MS)
                except Exception as exc:
                    Tool.write_log(f"Failed to terminate worker ({label}): {exc}")

        if self._is_worker_running(worker):
            Tool.write_log(f"Worker is still running after shutdown request: {label}")
            return False

        try:
            self._call_worker_method(worker, "deleteLater")
        except Exception as exc:
            Tool.write_log(f"Failed to schedule worker delete ({label}): {exc}")
        return True

    def _stop_qthread_worker_attr(self, attr_name: str) -> bool:
        worker = getattr(self, attr_name, None)
        if worker is None:
            return True

        stopped = self._stop_qthread_worker_instance(worker, attr_name)
        if stopped:
            try:
                setattr(self, attr_name, None)
            except Exception:
                pass
        return stopped

    def _stop_qthread_worker_dict(self, attr_name: str) -> bool:
        workers = getattr(self, attr_name, None)
        if not isinstance(workers, dict):
            return True

        all_stopped = True
        for worker in list(workers.keys()):
            stopped = self._stop_qthread_worker_instance(worker, attr_name)
            if stopped:
                workers.pop(worker, None)
            else:
                all_stopped = False
        return all_stopped

    def _stop_background_workers(self) -> bool:
        all_stopped = True
        for attr_name in self.BACKGROUND_WORKER_ATTRS:
            if not self._stop_qthread_worker_attr(attr_name):
                all_stopped = False
        for attr_name in self.BACKGROUND_WORKER_DICT_ATTRS:
            if not self._stop_qthread_worker_dict(attr_name):
                all_stopped = False
        return all_stopped

    def closeEvent(self, event):
        self._app_is_closing = True
        if not self._stop_background_workers():
            self._app_is_closing = False
            ignore = getattr(event, "ignore", None)
            if callable(ignore):
                ignore()
            return

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
