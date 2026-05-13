from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut


class ShortcutMixin:
    def _setup_shortcuts(self):
        self.ui.openTableMenuButton.setShortcut(QKeySequence("Ctrl+O"))
        self.ui.helpMenuButton.setShortcut(QKeySequence("F1"))
        self.ui.createDocMenuButton.setShortcut(QKeySequence("Ctrl+Shift+E"))

        def _bind(shortcut_text, callback, parent=None, context=None):
            shortcut = QShortcut(QKeySequence(shortcut_text), parent or self)
            if context is not None:
                shortcut.setContext(context)
            shortcut.activated.connect(callback)
            self._shortcuts.append(shortcut)
            return shortcut

        _bind("F1", self.show_help)
        _bind("Ctrl+O", self.openTable)
        _bind("Ctrl+Shift+E", self.exportDocs)
        _bind("Ctrl+F", self._focus_table_quick_search)
        _bind(
            "Ctrl+D",
            self._duplicate_selected_rows,
            parent=self.ui.KpTable,
            context=Qt.ShortcutContext.WidgetWithChildrenShortcut,
        )
        _bind(
            "Delete",
            self._delete_selected_rows,
            parent=self.ui.KpTable,
            context=Qt.ShortcutContext.WidgetWithChildrenShortcut,
        )
        _bind(
            "Ctrl+Return",
            self._fill_formula_to_selection,
            parent=self.ui.KpTable,
            context=Qt.ShortcutContext.WidgetWithChildrenShortcut,
        )
        _bind(
            "Ctrl+Enter",
            self._fill_formula_to_selection,
            parent=self.ui.KpTable,
            context=Qt.ShortcutContext.WidgetWithChildrenShortcut,
        )
        undo_shortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Undo), self.ui.KpTable)
        undo_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        undo_shortcut.activated.connect(self._undo_last_table_change)
        self._shortcuts.append(undo_shortcut)
