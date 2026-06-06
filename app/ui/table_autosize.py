from __future__ import annotations

from collections.abc import Mapping
from contextlib import contextmanager
from typing import Any

try:
    from PySide6.QtWidgets import QHeaderView, QTableWidget
except Exception:  # pragma: no cover - used by lightweight unit-test stubs
    QHeaderView = None

    class QTableWidget:  # type: ignore[no-redef]
        pass


DEFAULT_ROW_HEIGHT = 24
DEFAULT_LONG_TEXT_COLUMNS = {1: 300}
DEFAULT_FULL_RESIZE_ROW_LIMIT = 80
DEFAULT_MIN_COLUMN_WIDTH = 48
DEFAULT_MAX_COLUMN_WIDTH = 220
DEFAULT_MAX_ROW_HEIGHT = 120


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
        interactive = _resize_mode("Interactive")
        if callable(set_section_resize_mode) and interactive is not None:
            set_section_resize_mode(interactive)

    horizontal_header_getter = getattr(table, "horizontalHeader", None)
    horizontal_header = horizontal_header_getter() if callable(horizontal_header_getter) else None
    interactive = _resize_mode("Interactive")
    if horizontal_header is not None and interactive is not None:
        set_section_resize_mode = getattr(horizontal_header, "setSectionResizeMode", None)
        if callable(set_section_resize_mode):
            set_section_resize_mode(interactive)

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
    full_resize_row_limit: int = DEFAULT_FULL_RESIZE_ROW_LIMIT,
) -> None:
    configure_table_autosize(
        table,
        min_row_height=min_row_height,
        text_columns=text_columns,
    )

    row_count = _table_count(table, "rowCount")
    is_large_table = row_count is not None and row_count > int(full_resize_row_limit)

    if resize_columns:
        if is_large_table:
            _resize_columns_from_sample(table, text_columns, sample_limit=full_resize_row_limit)
        else:
            resize_columns_to_contents = getattr(table, "resizeColumnsToContents", None)
            if callable(resize_columns_to_contents):
                resize_columns_to_contents()
        _apply_fixed_text_column_widths(table, text_columns)

    _resize_rows_by_estimate(
        table,
        min_row_height=min_row_height,
        text_columns=text_columns,
    )

    refresh_table_viewport(table)


def refresh_table_viewport(table: QTableWidget, *, force_updates_enabled: bool = False) -> None:
    if force_updates_enabled:
        set_updates_enabled = getattr(table, "setUpdatesEnabled", None)
        if callable(set_updates_enabled):
            set_updates_enabled(True)

        viewport_getter = getattr(table, "viewport", None)
        viewport = viewport_getter() if callable(viewport_getter) else None
        viewport_set_updates_enabled = getattr(viewport, "setUpdatesEnabled", None)
        if callable(viewport_set_updates_enabled):
            viewport_set_updates_enabled(True)

    for method_name in ("doItemsLayout", "updateGeometries"):
        method = getattr(table, method_name, None)
        if callable(method):
            method()

    viewport_getter = getattr(table, "viewport", None)
    viewport = viewport_getter() if callable(viewport_getter) else None
    update = getattr(viewport, "update", None)
    if callable(update):
        update()

    table_update = getattr(table, "update", None)
    if callable(table_update):
        table_update()


def _table_count(table: QTableWidget, getter_name: str) -> int | None:
    getter = getattr(table, getter_name, None)
    if not callable(getter):
        return None
    try:
        return int(getter())
    except Exception:
        return None


def _text_width(table: QTableWidget, text: str) -> int:
    metrics_getter = getattr(table, "fontMetrics", None)
    metrics = metrics_getter() if callable(metrics_getter) else None
    horizontal_advance = getattr(metrics, "horizontalAdvance", None)
    if callable(horizontal_advance):
        return int(horizontal_advance(str(text)))
    return len(str(text)) * 7


def _resize_columns_from_sample(
    table: QTableWidget,
    text_columns: Mapping[int, int] | tuple[int, ...] | list[int] | None,
    *,
    sample_limit: int,
) -> None:
    set_column_width = getattr(table, "setColumnWidth", None)
    item_getter = getattr(table, "item", None)
    if not callable(set_column_width) or not callable(item_getter):
        return

    row_count = _table_count(table, "rowCount") or 0
    column_count = _table_count(table, "columnCount") or 0
    fixed_columns = _normalise_text_columns(text_columns)
    header_item_getter = getattr(table, "horizontalHeaderItem", None)
    rows_to_scan = min(row_count, max(0, int(sample_limit)))

    for column in range(column_count):
        if column in fixed_columns:
            continue

        max_width = DEFAULT_MIN_COLUMN_WIDTH
        if callable(header_item_getter):
            header_item = header_item_getter(column)
            header_text = header_item.text() if header_item is not None else ""
            max_width = max(max_width, _text_width(table, header_text) + 28)

        for row in range(rows_to_scan):
            item = item_getter(row, column)
            if item is None:
                continue
            text_getter = getattr(item, "text", None)
            text = text_getter() if callable(text_getter) else ""
            max_width = max(max_width, _text_width(table, text) + 28)

        width = min(max(max_width, DEFAULT_MIN_COLUMN_WIDTH), DEFAULT_MAX_COLUMN_WIDTH)
        set_column_width(column, width)


def _resize_rows_by_estimate(
    table: QTableWidget,
    *,
    min_row_height: int,
    text_columns: Mapping[int, int] | tuple[int, ...] | list[int] | None,
) -> None:
    row_count = _table_count(table, "rowCount") or 0
    set_row_height = getattr(table, "setRowHeight", None)
    fixed_columns = _normalise_text_columns(text_columns)

    if not callable(set_row_height):
        return

    for row in range(row_count):
        set_row_height(
            row,
            _estimated_row_height(
                table,
                row=row,
                min_row_height=min_row_height,
                fixed_columns=fixed_columns,
            ),
        )


def _line_spacing(table: QTableWidget) -> int:
    metrics_getter = getattr(table, "fontMetrics", None)
    metrics = metrics_getter() if callable(metrics_getter) else None
    line_spacing = getattr(metrics, "lineSpacing", None)
    if callable(line_spacing):
        return int(line_spacing())
    return 16


def _estimated_row_height(
    table: QTableWidget,
    *,
    row: int,
    min_row_height: int,
    fixed_columns: Mapping[int, int],
) -> int:
    if not fixed_columns:
        return int(min_row_height)

    item_getter = getattr(table, "item", None)
    if not callable(item_getter):
        return int(min_row_height)

    height = int(min_row_height)
    line_spacing = _line_spacing(table)
    for column, width in fixed_columns.items():
        item = item_getter(row, column)
        if item is None:
            continue
        text_getter = getattr(item, "text", None)
        text = str(text_getter() if callable(text_getter) else "")
        if not text:
            continue
        available_width = max(int(width) - 16, 1)
        text_width = _text_width(table, text)
        line_count = max(1, (text_width + available_width - 1) // available_width)
        height = max(height, min(DEFAULT_MAX_ROW_HEIGHT, line_count * line_spacing + 8))
    return height


@contextmanager
def table_update_guard(*tables: QTableWidget | None):
    restore_stack = []
    for table in tables:
        if table is None:
            continue

        set_sorting_enabled = getattr(table, "setSortingEnabled", None)
        is_sorting_enabled = getattr(table, "isSortingEnabled", None)
        sorting_enabled = None
        if callable(set_sorting_enabled) and callable(is_sorting_enabled):
            try:
                sorting_enabled = bool(is_sorting_enabled())
                set_sorting_enabled(False)
            except Exception:
                sorting_enabled = None

        viewport_getter = getattr(table, "viewport", None)
        viewport = viewport_getter() if callable(viewport_getter) else None
        viewport_set_updates_enabled = getattr(viewport, "setUpdatesEnabled", None)
        viewport_updates_enabled = getattr(viewport, "updatesEnabled", None)
        viewport_was_enabled = None
        if callable(viewport_set_updates_enabled):
            try:
                viewport_was_enabled = (
                    bool(viewport_updates_enabled()) if callable(viewport_updates_enabled) else True
                )
                viewport_set_updates_enabled(False)
            except Exception:
                viewport_was_enabled = None

        set_updates_enabled = getattr(table, "setUpdatesEnabled", None)
        updates_enabled = getattr(table, "updatesEnabled", None)
        table_updates_enabled = None
        if callable(set_updates_enabled):
            try:
                table_updates_enabled = bool(updates_enabled()) if callable(updates_enabled) else True
                set_updates_enabled(False)
            except Exception:
                table_updates_enabled = None

        restore_stack.append(
            (
                table,
                sorting_enabled,
                table_updates_enabled,
                viewport,
                viewport_was_enabled,
            )
        )

    try:
        yield
    finally:
        for table, sorting_enabled, table_updates_enabled, viewport, viewport_was_enabled in reversed(restore_stack):
            set_updates_enabled = getattr(table, "setUpdatesEnabled", None)
            if callable(set_updates_enabled) and table_updates_enabled is not None:
                set_updates_enabled(table_updates_enabled)

            viewport_set_updates_enabled = getattr(viewport, "setUpdatesEnabled", None)
            if callable(viewport_set_updates_enabled) and viewport_was_enabled is not None:
                viewport_set_updates_enabled(viewport_was_enabled)

            set_sorting_enabled = getattr(table, "setSortingEnabled", None)
            if callable(set_sorting_enabled) and sorting_enabled is not None:
                set_sorting_enabled(sorting_enabled)

            viewport_getter = getattr(table, "viewport", None)
            current_viewport = viewport_getter() if callable(viewport_getter) else viewport
            update = getattr(current_viewport, "update", None)
            if callable(update):
                update()
