from __future__ import annotations

from pathlib import Path


def force_excel_recalc(file_path: str) -> bool:
    """Return True when Excel was actively recalculated."""
    import platform

    normalized_path = str(Path(file_path).expanduser().resolve())
    system = platform.system()

    if system == "Windows":
        import win32com.client

        excel = None
        workbook = None
        try:
            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = False
            workbook = excel.Workbooks.Open(normalized_path)
            excel.CalculateFull()
            workbook.Save()
        finally:
            if workbook is not None:
                workbook.Close(SaveChanges=True)
            if excel is not None:
                excel.Quit()
        return True

    if system == "Darwin":
        return False

    raise RuntimeError("Автопересчет Excel поддерживается только на Windows")
