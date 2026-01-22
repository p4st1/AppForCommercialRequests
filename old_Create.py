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

if data[4]:
    self.headers.append('Срок доставки')

self.customerData = data[1][0]
self.extraData = data[2]

document = Document()

normal_style = document.styles['Normal']

font = normal_style.font
font.name = 'Times New Roman'
font.size = Pt(11)

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
run.add_picture(str(Config.logo_path), width=Cm(2))

right_cell = headerTable.cell(0, 1) 
right_paragraph = right_cell.paragraphs[0]

run_text = right_paragraph.add_run(f'''ООО "АЛЬФА КАППА ИНЖИНИРИНГ\nИНН 9731121825; КПП 772901001\n121471, Г.МОСКВА, УЛ., РЯБИНОВАЯ, Д.26 СТР.1, ПОМЕЩ.141\nalphakappa.ru, Тел: +7 (993) 338-47-22, admin@alphakappa.ru''')
run_text.font.size = Pt(7)

headerTable.style = 'Normal Table'

document.add_paragraph()

header_table = document.add_table(rows=3, cols=2)
header_table.alignment = WD_TABLE_ALIGNMENT.CENTER

cell_left = header_table.cell(0, 0)
cell_left.text = f"""Исх. №{data[3]}/{datetime.now().strftime('%d.%m')} от {datetime.now().strftime('%d.%m.%Y')}"""
cell_left.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT

cell_right = header_table.cell(2, 1)
cell_right.text = f'{self.customerData[2]} {self.customerData[1][0]}. {self.customerData[3][0]}.'
cell_right.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

cell_bottom = header_table.cell(1, 1)
cell_bottom.text = f'{self.customerData[7]}'
cell_bottom.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

cell_bottom = header_table.cell(0, 1)
cell_bottom.text = f'{self.customerData[8]}'
cell_bottom.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

for row in header_table.rows:
    row.height = Pt(15)
    for cell in row.cells:
        for paragraph in cell.paragraphs:
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.line_spacing = 1.0

document.add_paragraph()

p = document.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER

if self.customerData[10] == 'женский':
    sex = 'Уважаемая'
else:
    sex = 'Уважаемый'
    
run = p.add_run(f"""{sex} {self.customerData[1]} {self.customerData[3]} !""")
run.font.name = 'Times New Roman'
run.font.size = Pt(11)

p = document.add_paragraph(
    f"""    В ответ на заявку {self.extraData[0]} на поставку оборудования, высылаем Вам коммерческое предложение и готовы предложить продукцию в следующем ассортименте.
"""
)
run.font.name = 'Times New Roman'
p.paragraph_format.first_line_indent = Pt(18)
p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
run.font.size = Pt(11)


table = document.add_table(rows=self.rows + 1, cols=len(self.headers))
table.style = "Table Grid"

cols = [0.77, 2.98, 2.69, 1.03, 1.22, 3, 3, 3, 0.1, 0.1,]

for i in range(len(self.headers)):
    for cell in table.columns[i].cells:
        cell.width = Cm(cols[i])

for col in range(len(self.headers)):
    cell = table.cell(0, col)
    cell.text = self.headers[col]
    paragraph = cell.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    run = paragraph.runs[0]
    run.font.size = Pt(11)
    run.font.name = run.font.name = 'Times New Roman'
    run.font.bold = True
    
    
for row in range(self.rows):
    for col in range(len(self.headers)):
        cell = table.cell(row + 1, col)
        cell.text = self.table[row][col]
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        run = paragraph.runs[0]
        run.font.size = Pt(11)
        run.font.name = 'Times New Roman'

table.add_row()
row = table.rows[len(self.table) + 1]
row.cells[0].merge(row.cells[5])

cell = table.cell(len(self.table) + 1, 0)
cell.text = 'Итого'
paragraph = cell.paragraphs[0]
paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
table.rows[len(self.table) + 1].height = Cm(0.7)
run = paragraph.runs[0]
run.font.size = Pt(11)
run.font.name = 'Times New Roman'

result = [[self.table[0][6][0], 0], [self.table[0][6][0], 0]]

delivery_min = 0

for item in self.table:
    result[0][1] += float(item[6][1:].replace(',', '.'))
    result[1][1] += float(item[7][1:].replace(',', '.'))
    if int(item[8].split()[0]) > delivery_min:
        delivery_min = int(item[8].split()[0])

cell = table.cell(len(self.table) + 1, 6)
cell.text = f"{result[0][0]}{str(round(result[0][1], 2)).replace('.', ',')}"
paragraph = cell.paragraphs[0]
paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
run = paragraph.runs[0]
run.font.size = Pt(11)
run.font.name = 'Times New Roman'

cell = table.cell(len(self.table) + 1, 7)
cell.text = f"{result[1][0]}{str(result[1][1]).replace('.', ',')}"
paragraph = cell.paragraphs[0]
paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
run = paragraph.runs[0]
run.font.size = Pt(11)
run.font.name = 'Times New Roman'

result.append([result[1][0], result[1][1] - result[0][1]])

tool = ExtraTools()

p = document.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
p.paragraph_format.line_spacing = 1.15

run = p.add_run(f"""\n{str(round(result[0][1], 2)).replace('.', ',')} {Config.currency[result[1][0]][0]} ({tool.decimal2text(result[0][1],
                int_units=Config.currency[result[1][0]][1],
                exp_units=Config.currency[result[1][0]][2])}), включая НДС ({Tools.load_json(Config.vars_path)['parameters']['1'][1]}%) в сумме {str(round(result[2][1],2 )).replace('.', ',')} {Config.currency[result[1][0]][0]} ({tool.decimal2text(result[2][1],
                int_units=Config.currency[result[1][0]][1],
                exp_units=Config.currency[result[1][0]][2])})""")
run.font.bold = True
run.font.name = 'Times New Roman'
run.font.size = Pt(11)

if self.extraData[4] == '':
    self.extraData[4] = '0'

items = [
    (f"Условия поставки: {self.customerData[9]}", ''),
    
    (f"Срок гарантии - {self.extraData[1]} с момента отгрузки гарантия не распространяется на быстроизнашивающиеся части;", ''),
    
    (f"Сроки поставки - от {delivery_min} до {delivery_min + int(self.extraData[4])} дней с момента подписания спецификации с возможностью досрочной поставки;", ""),
    
    (f"Производитель - {self.extraData[3]};", ""),
    
    (f"Условия оплаты: посланная в течение {self.extraData[2]} с момента поставки;", ""),
    
    (f"Оплата осуществляется в Рублях РФ по курсу Центрального банка РФ {data[-1]}", ""),
    
    (f"Срок действия КП до {(datetime.now() + timedelta(days=10)).strftime('%d.%m.%Y')}.", "")
]

for main_text, sub_text in items:
    p = document.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.5)
    p.paragraph_format.first_line_indent = Inches(-0.25)
    p.paragraph_format.line_spacing = 1.15
    
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

footer_table = document.add_table(rows=2, cols=4)
footer_table.alignment = WD_TABLE_ALIGNMENT.CENTER

cell_left = footer_table.cell(0, 0)
cell_left.text = f"""С уважением,\nГенеральный директор"""
cell_left.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT

cell_mid = footer_table.cell(0, 1)        
left_paragraph = cell_mid.paragraphs[0]
run = left_paragraph.add_run()
run.add_picture(str(Config.print_path))
cell_mid.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT

cell_mid = footer_table.cell(0, 2)        
left_paragraph = cell_mid.paragraphs[0]
run = left_paragraph.add_run()
run.add_picture(str(Config.sign_path))
cell_mid.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT

cell_right = footer_table.cell(0, 3)
cell_right.text = f'Иванов И. И.'
cell_right.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT