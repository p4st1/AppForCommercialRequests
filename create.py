from docx import Document
from docx.shared import Inches
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from datetime import datetime

class createTextFile:
    def __init__(self, data):
        print(data)
        self.rows = data[0]
        self.cols = data[1]
        self.table = data[2]
        self.headers = ['№',
                        'Наименование',
                        'Каталожный товар',
                        'Ед. изм',
                        'Кол-во',
                        'Цена за ед. без НДС',
                        'Итого без НДС',
                        'Логистика',
                        'Таможня',
                        'Цена за ед.',
                        'Цена реализации за ед. без ндс',
                        'Итого реализации',
                        'Итого реализации без НДС',
                        'Итого реализации c НДС',
                        'Срок поставки',
                        'Срок поставщика'
                        ]
        
        document = Document()
        

        section = document.sections[0]
        
        section.left_margin = Cm(3)
        section.right_margin = Cm(1.5)
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        
        header = document.sections[0].header
        
        header.paragraphs[0].text = f'''ООО "АЛЬФА КАППА ИНЖИНИРИНГ\nИНН 9731121825; КПП 772901001\n121471, Г.МОСКВА, УЛ., РЯБИНОВАЯ, Д.26 СТР.1, ПОМЕЩ.141\nalphakappa.ru, Тел: +7 (993) 338-47-22, admin@alphakappa.ru'''
        header.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
        header.paragraphs[0].paragraph_format.left_indent = Cm(6.5)
        for run in header.paragraphs[0].runs:
            run.font.size = Pt(8)
        
        p = document.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        run = p.add_run(f"""\nИсх. №2/22.10 от {datetime.now().strftime('%d.%m.%Y')}""")
        p.add_run('\t')
        run = p.add_run(f'Должность ООО\n""\n')
        run.font.size = Pt(11)
        
        tab_stops = p.paragraph_format.tab_stops
        tab_stops.add_tab_stop(Inches(6), alignment=2)
         
        p = document.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        run = p.add_run(f"""Уважаемый (ая) Имя Отчество !""")
        run.font.name = 'Times New Roman'
        run.font.size = Pt(11)
        
        p = document.add_paragraph(
            f"""В ответ на заявку 105465-ТТ на поставку оборудования, высылаем Вам коммерческое предложение и готовы предложить продукцию в следующем ассортименте.
"""
        )
        run.font.name = 'Times New Roman'
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        run.font.size = Pt(11)
        

        table = document.add_table(rows=self.rows + 1, cols=self.cols)
        table.style = "Table Grid"

        for col in table.columns:
            col.width = Inches(3)

        table.columns[1].width = Inches(4)

        for col in range(self.cols):
            cell = table.cell(0, col)
            cell.text = self.headers[col]
            paragraph = cell.paragraphs[0]
            run = paragraph.runs[0]
            run.font.size = Pt(8)
            run.font.name = run.font.name = 'Calibri'
            
        for row in range(self.rows):
            for col in range(self.cols):
                cell = table.cell(row + 1, col)
                cell.text = self.table[row][col]
                paragraph = cell.paragraphs[0]
                run = paragraph.runs[0]
                run.font.size = Pt(8)
                run.font.name = 'Calibri'

        p = document.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        run = p.add_run(f"""\n459 223,31 CNY (четыреста пятьдесят девять тысяч двести двадцать три) юаня 31 фэнь, включая НДС (20%) в сумме 76 537,22 CNY (семьдесят шесть тысяч пятьсот тридцать семь) юаней 22 фэня""")
        run.font.bold = True
        run.font.name = 'Times New Roman'
        run.font.size = Pt(12)
        
        items = [
            ("Условия поставки: DDP", 
            "Срок гарантии - 12 месяцев с момента отгрузки гарантия не распространяется на быстроизнашивающиеся части;"),
            
            ("Сроки поставки - до 75 дней с момента подписания спецификации с возможностью досрочной поставки;", ""),
            
            ("Производитель - CAT, OEM;", ""),
            
            ("Условия оплаты: посланная в течение 60 календарных дней с момента поставки;", ""),
            
            ("Оплата осуществляется в Рублик РФ по курсу Центрального банка РФ на дату подписания спецификации Поставщиком;", ""),
            
            ("Срок действия КП до 01.11.2025.", "")
        ]
        
        for main_text, sub_text in items:
            p = document.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.5)
            p.paragraph_format.first_line_indent = Inches(-0.25)
            
            run = p.add_run('- ')
            run.font.name = 'Symbol'
            
            run2 = p.add_run(main_text)
            run2.font.name = 'Times New Roman'
            run2.font.size = Pt(11)
            if sub_text:
                p2 = document.add_paragraph()
                p2.paragraph_format.left_indent = Inches(0.75)
                p2.paragraph_format.first_line_indent = Inches(-0.25)
                
                run3 = p2.add_run('  ' + sub_text)
                run3.font.name = 'Times New Roman'
                run3.font.size = Pt(11)
                
        p = document.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(f"""С уважением,\nГениральнай директор""")
        run.font.size = Pt(11)

        document.save("kp1.docx")
