from docx import Document
from docx.shared import Inches
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from utilities.tools import DatabaseTools as Tools
from datetime import datetime, timedelta
from utilities.config import Config

class createTextFile:
    def __init__(self, data):
        tableData = data[0]
        self.rows = tableData[0]
        self.table = tableData[1]
        self.headers = ['№',
                        'Наименование',
                        'Каталожный товар',
                        'Ед. изм',
                        'Кол-во',
                        'Цена за ед. без ндс',
                        'Итого без НДС',
                        'Итого c НДС',
                        ]
        
        self.customerData = data[1][0]
        self.extraData = data[2]
        document = Document()

        section = document.sections[0]
        
        section.left_margin = Cm(3)
        section.right_margin = Cm(1.5)
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        
        header = document.sections[0].header
        
        for paragraph in header.paragraphs:
            paragraph.clear()
        
        headerTable = header.add_table(rows=1, cols=2, width=Cm(15))

        left_cell = headerTable.cell(0, 0) 
        left_paragraph = left_cell.paragraphs[0]
        run = left_paragraph.add_run()
        run.add_picture('logo.jpg', width=Cm(3))
        

        right_cell = headerTable.cell(0, 1) 
        right_paragraph = right_cell.paragraphs[0]

        run_text = right_paragraph.add_run(f'''ООО "АЛЬФА КАППА ИНЖИНИРИНГ\nИНН 9731121825; КПП 772901001\n121471, Г.МОСКВА, УЛ., РЯБИНОВАЯ, Д.26 СТР.1, ПОМЕЩ.141\nalphakappa.ru, Тел: +7 (993) 338-47-22, admin@alphakappa.ru''')
        run_text.font.size = Pt(8)
        
        headerTable.style = 'Normal Table'
    
        
        p = document.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        run = p.add_run(f"""\nИсх. №{data[3]}/{datetime.now().strftime('%d.%m')} от {datetime.now().strftime('%d.%m.%Y')}""")
        p.add_run('\t')
        run = p.add_run(f'{self.customerData[7]}\n')
        p.add_run('\t')
        run = p.add_run(f'{self.customerData[8]}\n')
        run.font.size = Pt(11)
        
        tab_stops = p.paragraph_format.tab_stops
        tab_stops.add_tab_stop(Inches(6), alignment=2)
         
        p = document.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        run = p.add_run(f"""Уважаемый (ая) {self.customerData[1]} {self.customerData[3]} !""")
        run.font.name = 'Times New Roman'
        run.font.size = Pt(11)
        
        p = document.add_paragraph(
            f"""В ответ на заявку {self.extraData[0]} на поставку оборудования, высылаем Вам коммерческое предложение и готовы предложить продукцию в следующем ассортименте.
"""
        )
        run.font.name = 'Times New Roman'
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        run.font.size = Pt(11)
        

        table = document.add_table(rows=self.rows + 1, cols=len(self.headers))
        table.style = "Table Grid"

        for col in table.columns:
            col.width = Inches(3)

        table.columns[1].width = Inches(4)

        for col in range(len(self.headers)):
            cell = table.cell(0, col)
            cell.text = self.headers[col]
            paragraph = cell.paragraphs[0]
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = paragraph.runs[0]
            run.font.size = Pt(11)
            run.font.name = run.font.name = 'Calibri'
            run.font.bold = True
            
            
        for row in range(self.rows):
            for col in range(len(self.headers)):
                cell = table.cell(row + 1, col)
                cell.text = self.table[row][col]
                paragraph = cell.paragraphs[0]
                run = paragraph.runs[0]
                run.font.size = Pt(11)
                run.font.name = 'Calibri'

        p = document.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        run = p.add_run(f"""\n459 223,31 CNY (четыреста пятьдесят девять тысяч двести двадцать три) юаня 31 фэнь, включая НДС (20%) в сумме 76 537,22 CNY (семьдесят шесть тысяч пятьсот тридцать семь) юаней 22 фэня""")
        run.font.bold = True
        run.font.name = 'Times New Roman'
        run.font.size = Pt(12)
        
        items = [
            (f"Условия поставки: {self.customerData[9]}", ''),
            
            (f"Срок гарантии - {self.extraData[1]} с момента отгрузки гарантия не распространяется на быстроизнашивающиеся части;", ''),
            
            ("Сроки поставки - до 75 дней с момента подписания спецификации с возможностью досрочной поставки;", ""),
            
            (f"Производитель - {self.extraData[3]};", ""),
            
            (f"Условия оплаты: посланная в течение {self.extraData[2]} с момента поставки;", ""),
            
            ("Оплата осуществляется в Рублик РФ по курсу Центрального банка РФ на дату подписания спецификации Поставщиком;", ""),
            
            (f"Срок действия КП до {(datetime.now() + timedelta(days=10)).strftime('%d.%m.%Y')}.", "")
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

        try:
            document.save(f"{Tools.resourcePath(Config.config['pathToSaveCP'])}/КП_от_{datetime.now().strftime('%d.%m.%Y')}.docx")
        except Exception as e:
            print(e)
