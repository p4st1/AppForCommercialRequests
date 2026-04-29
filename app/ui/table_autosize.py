from __future__ import annotations

from collections.abc import Mapping
from typing import Any

try:
    from PySide6.QtWidgets import QHeaderView, QTableWidget
except Exception:  # pragma: no cover - used by lightweight unit-test stubs
    QHeaderView = None

    class QTableWidget:  # type: ignore[no-redef]
        pass


DEFAULT_ROW_HEIGHT = 24
DEFAULT_LONG_TEXT_COLUMNS = {1: 300}


def _resize_mode(mode_name: str) -> Any:
    if QHeaderView is None:
        return None
    resize_mode = getattr(QHeaderView, "ResizeMode", None)
    if resize_mode is not None:
        return getattr(resize_mode, mode_name, None)
    return getattr(QHeaderView, mode_name, None)


def _normalise_text_columns(
    text_columns: Mapping[int, int] | tuple[int, ...] | list[int] | None,
) -> dict[int, int]:
    if text_columns is None:
        return {}
    if isinstance(text_columns, Mapping):
        return {int(column): int(width) for column, width in text_columns.items()}
    return {int(column): DEFAULT_LONG_TEXT_COLUMNS.get(int(column), 300) for column in text_columns}


def configure_table_autosize(
    table: QTableWidget,
    *,
    min_row_height: int = DEFAULT_ROW_HEIGHT,
    text_columns: Mapping[int, int] | tuple[int, ...] | list[int] | None = DEFAULT_LONG_TEXT_COLUMNS,
) -> None:
    set_word_wrap = getattr(table, "setWordWrap", None)
    if callable(set_word_wrap):
        set_word_wrap(True)

    vertical_header_getter = getattr(table, "verticalHeader", None)
    vertical_header = vertical_header_getter() if callable(vertical_header_getter) else None
    if vertical_header is not None:
        set_default_section_size = getattr(vertical_header, "setDefaultSectionSize", None)
        if callable(set_default_section_size):
            set_default_section_size(int(min_row_height))
        set_minimum_section_size = getattr(vertical_header, "setMinimumSectionSize", None)
        if callable(set_minimum_section_size):
            set_minimum_section_size(int(min_row_height))
        set_section_resize_mode = getattr(vertical_header, "setSectionResizeMode", None)
        resize_to_contents = _resize_mode("ResizeToContents")
        if callable(set_section_resize_mode) and resize_to_contents is not None:
            set_section_resize_mode(resize_to_contents)

    horizontal_header_getter = getattr(table, "horizontalHeader", None)
    horizontal_header = horizontal_header_getter() if callable(horizontal_header_getter) else None
    resize_to_contents = _resize_mode("ResizeToContents")
    if horizontal_header is not None and resize_to_contents is not None:
        set_section_resize_mode = getattr(horizontal_header, "setSectionResizeMode", None)
        if callable(set_section_resize_mode):
            set_section_resize_mode(resize_to_contents)

    _apply_fixed_text_column_widths(table, text_columns)


def _apply_fixed_text_column_widths(
    table: QTableWidget,
    text_columns: Mapping[int, int] | tuple[int, ...] | list[int] | None,
) -> None:
    columns = _normalise_text_columns(text_columns)
    if not columns:
        return

    column_count_getter = getattr(table, "columnCount", None)
    column_count = column_count_getter() if callable(column_count_getter) else 0
    horizontal_header_getter = getattr(table, "horizontalHeader", None)
    horizontal_header = horizontal_header_getter() if callable(horizontal_header_getter) else None
    interactive = _resize_mode("Interactive")
    set_column_width = getattr(table, "setColumnWidth", None)

    for column, width in columns.items():
        if column < 0 or (column_count and column >= column_count):
            continue
        if horizontal_header is not None and interactive is not None:
            set_section_resize_mode = getattr(horizontal_header, "setSectionResizeMode", None)
            if callable(set_section_resize_mode):
                set_section_resize_mode(column, interactive)
        if callable(set_column_width):
            set_column_width(column, int(width))


def resize_table_to_contents(
    table: QTableWidget,
    *,
    min_row_height: int = DEFAULT_ROW_HEIGHT,
    text_columns: Mapping[int, int] | tuple[int, ...] | list[int] | None = DEFAULT_LONG_TEXT_COLUMNS,
    resize_columns: bool = True,
) -> None:
    configure_table_autosize(
        table,
        min_row_height=min_row_height,
        text_columns=text_columns,
    )

    if resize_columns:
        resize_columns_to_contents = getattr(table, "resizeColumnsToContents", None)
        if callable(resize_columns_to_contents):
            resize_columns_to_contents()
        _apply_fixed_text_column_widths(table, text_columns)

    resize_rows_to_contents = getattr(table, "resizeRowsToContents", None)
    if callable(resize_rows_to_contents):
        resize_rows_to_contents()

    viewport_getter = getattr(table, "viewport", None)
    viewport = viewport_getter() if callable(viewport_getter) else None
    update = getattr(viewport, "update", None)
    if callable(update):
        update()
