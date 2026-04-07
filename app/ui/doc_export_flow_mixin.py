from createDocument import mainWindow as createDocWindow
from config import Config
from tools import DatabaseTools as Tool


class DocExportFlowMixin:
    def openCreateDocWindow(self, tableData):
        window = createDocWindow(self, tableData=tableData)
        window.ui.numLine.setText(self.ui.requestNumberLine.text().strip())
        window.show()
        window.windowClosed.connect(self.updateHistoryTable)
        if Config.settings["closeTable"]:
            window.windowClosed.connect(self.closeTable)
            self.ui.KpTable.setRowCount(0)

    def exportDocs(self):
        if not Config.isTableOpened:
            self.error("Ошибка", "Загрузите КП поставщика")
            return
        if self._has_mixed_currencies():
            self.error(
                "Ошибка",
                "Создание КП в DOCX для таблицы со смешанной валютой не поддерживается.",
            )
            return

        Tool.write_log("CREATING DOCX")
        table_data = self.getTableData()
        self.openCreateDocWindow((len(table_data), table_data))
        Tool.write_log("CREATING DOCX...")
