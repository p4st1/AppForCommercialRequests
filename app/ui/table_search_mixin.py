from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton


class TableSearchMixin:
    def _setup_table_quick_search(self):
        self.tableQuickSearchLine = QLineEdit(self)
        self.tableQuickSearchLine.setPlaceholderText("Быстрый поиск по таблице (Ctrl+F)")
        self.tableQuickSearchClearButton = QPushButton("Сброс", self)
        self.tableQuickSearchClearButton.setMinimumWidth(82)

        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 6)
        search_layout.addWidget(self.tableQuickSearchLine, 1)
        search_layout.addWidget(self.tableQuickSearchClearButton, 0)
        self.ui.verticalLayout_2.insertLayout(0, search_layout)

        self.tableQuickSearchLine.textChanged.connect(self._on_table_quick_search_changed)
        self.tableQuickSearchClearButton.clicked.connect(self.tableQuickSearchLine.clear)

    def _on_table_quick_search_changed(self, text):
        self.quickSearchText = str(text or "").strip().casefold()
        self._apply_table_filters()

    def _focus_table_quick_search(self):
        self.ui.tabWidget.setCurrentWidget(self.ui.tab)
        self.tableQuickSearchLine.setFocus()
        self.tableQuickSearchLine.selectAll()
