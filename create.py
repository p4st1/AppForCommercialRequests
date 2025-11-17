from docx import Document
from docx.shared import Inches
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH


class createTextFile:

    def __init__(self, data):
        self.rows = data[0]
        self.cols = data[1]
        self.table = data[2]

        document = Document()
        p = document.add_paragraph(f"""Уважаемый (ая) Имя Отчество !""")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        p = document.add_paragraph(
            f"""В ответ на заявку 105465-ТТ на поставку оборудования, высылаем Вам коммерческое предложение и готовы предложить продукцию в следующем ассортименте.
"""
        )
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT

        table = document.add_table(rows=self.rows, cols=self.cols)
        table.style = "Table Grid"

        for col in table.columns:
            col.width = Inches(3)

        table.columns[1].width = Inches(4)

        for row in range(self.rows):
            for col in range(self.cols):
                cell = table.cell(row, col)
                cell.text = self.table[row][col]
                paragraph = cell.paragraphs[0]
                run = paragraph.runs[0]
                run.font.size = Pt(8)
                run.font.name = "Arial"

        document.add_page_break()

        document.save("kp1.docx")
