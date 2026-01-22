from docx import Document
from decimal import Decimal, ROUND_HALF_UP
from tools import DatabaseTools as Tools
from tools import Tools as ExtraTools
from datetime import datetime, timedelta
import copy
from openpyxl import load_workbook
from openpyxl.styles import Border, Side, Alignment
from config import Config
import shutil
import os

class createTextFile:
    def __init__(self, docxData):
        Tools.write_log(f"Docx path to save: {Tools.resourcePath(Config.config['pathToSaveCP'])}")
        Tools.write_log('INIT DOCX...')
        
        tableData = docxData[0][1]
        customerData = docxData[1][0]
        extraData = docxData[2]
        dbData = docxData[3]
        lastCol = docxData[4]
        condData = docxData[5]
        
        sum1, sum2, = 0, 0
        
        tool = ExtraTools()
        
        minDays, maxDays = 10 ** 4, 0
        
        for i in docxData:
            print(i)
            
        for i in tableData:
            print(i, int(i[8].split()[0]))
            sum1 += float(i[6][1:].replace(',', '.'))
            sum2 += float(i[7][1:].replace(',', '.'))
            currency = i[6][0]
            if int(i[8].split()[0]) > maxDays:
                maxDays = int(i[8].split()[0])
            if int(i[8].split()[0]) < minDays:
                minDays = int(i[8].split()[0]) 
        
        currency = Config.currency[currency]
        
  
        def _replace_in_paragraph(paragraph, mapping: dict[str, str]) -> None:
            # ВАЖНО: заменяем по run'ам, чтобы не убить форматирование
            for run in paragraph.runs:
                for k, v in mapping.items():
                    if k in run.text:
                        run.text = run.text.replace(k, v)


        def _replace_everywhere(doc: Document, mapping: dict[str, str]) -> None:
            # body paragraphs
            for p in doc.paragraphs:
                _replace_in_paragraph(p, mapping)

            # tables in body
            for t in doc.tables:
                for row in t.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            _replace_in_paragraph(p, mapping)

            # headers/footers
            for sec in doc.sections:
                for p in sec.header.paragraphs:
                    _replace_in_paragraph(p, mapping)
                for p in sec.footer.paragraphs:
                    _replace_in_paragraph(p, mapping)


        def _set_cell_text_preserve(cell, text: str) -> None:
            # Не используем cell.text = ..., иначе слетит формат.
            p = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
            if p.runs:
                p.runs[0].text = text
                # очистим остальные run'ы, если есть
                for r in p.runs[1:]:
                    r.text = ""
            else:
                p.add_run(text)


        def _remove_row(table, row_idx: int) -> None:
            table._tbl.remove(table.rows[row_idx]._tr)


        def _fmt_money(v) -> str:
            # формат как в шаблоне: 1,57 (запятая) + знак ¥
            x = Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            s = f"{x:.2f}".replace(".", ",")
            return f"¥{s}"


        def fill_doc_like_template(
            template_path: str,
            output_path: str,
        ) -> None:
            doc = Document(template_path)

            gender = {
                'мужской': "ый",
                'женский': "ая"
            }
            
            data = {
                # header
                "ООО «АЛЬФА КАППА ИНЖИНИРИНГ»": "ООО «АЛЬФА КАППА ИНЖИНИРИНГ»",
                "ИНН 9731121825; КПП 772901001": "ИНН 9731121825; КПП 772901001",
                "121471, Г.МОСКВА, УЛ., РЯБИНОВАЯ, Д.26 СТР.1, ПОМЕЩ.141": "121471, Г.МОСКВА, УЛ., РЯБИНОВАЯ, Д.26 СТР.1, ПОМЕЩ.141",
                "alphakappa.ru": "alphakappa.ru",
                "+7 (993) 338-47-22": "+7 (993) 338-47-22",
                "admin@alphakappa.ru": "admin@alphakappa.ru",

                # body/table 0
                "Исх. №9/19.01 от 19.01.2026": f"Исх. №{docxData[3]}/{datetime.now().strftime('%d.%m')} от {datetime.now().strftime('%d.%m.%Y')}",
                "Директору": customerData[8],
                "ООО Сусуман": customerData[7],
                "Иванов И. И.": f"{customerData[1]} {customerData[2][0]}. {customerData[3][0]}." ,

                # greeting + text
                "Уважаемая Иван Иваныч !": f"Уважаем{gender[customerData[10]]} {customerData[1]} {customerData[3]} !",
                
                "заявку 123": f"заявку {extraData[0]}",

                # totals paragraph + terms
                "4,71 CNY ": f"{_fmt_money(sum1)} {currency[0]} ",
                "0,93 CNY": f"{_fmt_money(sum2 - sum1)} {currency[0]}",
                
                "(четыре юаня семьдесят одна фэнь)": f"({tool.decimal2text(sum1,
                int_units=currency[1],
                exp_units=currency[2])})",
                "(ноль юаней девяносто три фэня)": f"({tool.decimal2text(sum2 - sum1,
                int_units=currency[1],
                exp_units=currency[2])})",
                
                "(20%)": f"({Tools.load_json(Config.vars_path)['parameters']['1'][1]}%)",

                "Условия поставки: ": f"Условия поставки: {customerData[9]}",
                
                "Срок гарантии - 123": f"Срок гарантии - {extraData[1]}",
                
                "Производитель - 123;": f"Производитель - {extraData[3]};",
                
                "в течение 123": f"в течение {extraData[2]}",
                
                "Сроки поставки - от 70 до 193 дней с момента подписания спецификации с возможностью досрочной поставки;": f"Сроки поставки - от {minDays} до {maxDays} дней с момента подписания спецификации с возможностью досрочной поставки;",
                
                "Оплата осуществляется в Рублях РФ по курсу Центрального банка РФ на дату оплаты": f"Оплата осуществляется в Рублях РФ по курсу Центрального банка РФ {docxData[5]}",
                
                "Срок действия КП до 29.01.2026.": f"Срок действия КП до {(datetime.now() + timedelta(days=10)).strftime('%d.%m.%Y')}.",

                # signature
                "Гениральнай директор": "Гениральнай директор",
                "А. О. Кадыров": "А. О. Кадыров",
            }

            # ====== 1) Глобальные замены (если ты хочешь менять поля) ======
            _replace_everywhere(doc, data)

            # ====== 2) Таблица с товарами: пересобрать строки по списку items, сохранив формат 1-в-1 ======
            # В твоем файле это doc.tables[1]
            products = doc.tables[1]

            # Сохраняем XML-шаблон одной товарной строки (строка 1)
            row_template_tr = copy.deepcopy(products.rows[1]._tr)

            # Удаляем все товарные строки между заголовком и итогом
            # Останутся: row 0 (шапка) и last row (итого)
            while len(products.rows) > 2:
                _remove_row(products, 1)

            # Товары (как в файле, чтобы вышло 1-в-1)
            items = [
            
            ]
            
            for item in tableData:
                items.append(
                    {"name": item[1],
                     "sku": item[2],
                     "unit": item[3],
                     "qty": item[4],
                    "price": item[5].replace(',', '.')[1:],
                    "price2": item[6].replace(',', '.')[1:],
                    "price3": item[7].replace(',', '.')[1:],
                    "days": item[8]}
                )                

            totals_tr = products.rows[-1]._tr
            total_wo = Decimal("0.00")
            total_w = Decimal("0.00")

            for i, it in enumerate(items, start=1):
                new_tr = copy.deepcopy(row_template_tr)
                totals_tr.addprevious(new_tr)

                # только что вставленная строка всегда станет предпоследней
                r = products.rows[-2]

                price = Decimal(str(it["price"]))
                qty = Decimal(str(it["qty"]))
                row_wo = (price * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                row_w = (row_wo * Decimal("1.20")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                total_wo += Decimal(it["price2"])
                total_w += Decimal(it["price3"])

                _set_cell_text_preserve(r.cells[0], str(i))
                _set_cell_text_preserve(r.cells[1], it["name"])
                _set_cell_text_preserve(r.cells[2], it["sku"])
                _set_cell_text_preserve(r.cells[3], it["unit"])
                _set_cell_text_preserve(r.cells[4], str(it["qty"]))
                _set_cell_text_preserve(r.cells[5], _fmt_money(str(it["price"])))
                _set_cell_text_preserve(r.cells[6], _fmt_money(str(it["price2"])))
                _set_cell_text_preserve(r.cells[7], _fmt_money(str(it["price3"])))
                _set_cell_text_preserve(r.cells[8], it["days"])

            # Итоговая строка (в шаблоне первые 6 колонок уже слиты)
            total_row = products.rows[-1]
            _set_cell_text_preserve(total_row.cells[0], "Итого")
            _set_cell_text_preserve(total_row.cells[6], _fmt_money(total_wo))
            _set_cell_text_preserve(total_row.cells[7], _fmt_money(total_w))
            
            doc.save(output_path)
        
        fill_doc_like_template(Config.template_docx_path, f"{Tools.resourcePath(Config.config['pathToSaveCP'])}/КП_от_{datetime.now().strftime('%d.%m.%Y')}_.docx")
        
        try:
            Tools.write_log("creating docx File...")
            Tools.write_log(f"saving docx to: {Tools.resourcePath(Config.config['pathToSaveCP'])}")
            #{docxData[3]}
            
        except Exception as e:
            Tools.write_log(f"Unnable to save Docx: {e}")
            print(e)

class createExcelFile:
    def __init__(self, data):
        indent = int(Config.config['ExcelIndent'])
        newFilePath = f"{Tools.resourcePath(Config.config['pathToSaveExcel'])}/таблица_от_{datetime.now().strftime('%d_%m_%Y')}.xlsx"
        shutil.copy2(Config.template_path, newFilePath)
        wb = load_workbook(newFilePath)
        workSheet = wb.active
        
        dataTable = data[0]
        for row in range(len(dataTable)):
            currency = dataTable[row][5][0]
            workSheet[f'A{row + 2 + indent}'] = int(dataTable[row][0])
            workSheet[f'B{row + 2 + indent}'] = dataTable[row][1]
            workSheet[f'C{row + 2 + indent}'] = int(dataTable[row][2])
            workSheet[f'D{row + 2 + indent}'] = dataTable[row][3]
            workSheet[f'E{row + 2 + indent}'] = int(dataTable[row][4])
            workSheet[f'F{row + 2 + indent}'] = float(dataTable[row][5][1:].replace(',', '.'))
            workSheet[f'F{row + 2 + indent}'].number_format = f'"{currency}"#,##0.00'
            workSheet[f'G{row + 2 + indent}'] = f'=F{row + 2 + indent}*E{row + 2 + indent}'
            workSheet[f'G{row + 2 + indent}'].number_format = f'"{currency}"#,##0.00'
        
        workSheet[f'G{len(dataTable) + 2 + indent}'] = f'=SUM(G{2 + indent}:G{len(dataTable) + 1 + indent})'
        workSheet[f'G{len(dataTable) + 2 + indent}'].number_format = f'"{currency}"#,##0.00' 
        
        for row in range(len(dataTable)):
            if data[1][0] == 0:
                workSheet[f'H{row + 2 + indent}'] = f'=G{row + 2 + indent}*{data[1][1]}'
            if data[1][0] == 1:
                workSheet[f'H{row + 2 + indent}'] = f'=G{row + 2 + indent}+{int(data[1][1])}/G{len(dataTable) + 2 + indent}*G{row + 2 + indent}'
            workSheet[f'H{row + 2 + indent}'].number_format = f'"{currency}"#,##0.00' 
            
        workSheet[f'H{len(dataTable) + 2 + indent}'] = f'=SUM(H{2 + indent}:H{len(dataTable) + 1 + indent})'
        workSheet[f'H{len(dataTable) + 2 + indent}'].number_format = f'"{currency}"#,##0.00'
        workSheet[f'I{len(dataTable) + 2 + indent}'] = f'=SUM(I{2 + indent}:I{len(dataTable) + 1 + indent})'
        workSheet[f'I{len(dataTable) + 2 + indent}'].number_format = f'"{currency}"#,##0.00'
        workSheet[f'H{len(dataTable) + 3 + indent}'] = f'=H{len(dataTable) + 2 + indent}-G{len(dataTable) + 2 + indent}'
        workSheet[f'H{len(dataTable) + 3 + indent}'].number_format = f'"{currency}"#,##0.00' 
        
        for row in range(len(dataTable)):
            workSheet[f'I{row + 2 + indent}'] = f'=H{row + 2 + indent}*{data[2]}'
            workSheet[f'I{row + 2 + indent}'].number_format = f'"{currency}"#,##0.00'
            workSheet[f'J{row + 2 + indent}'] = f'=I{row + 2 + indent}/E{row + 2 + indent}'
            workSheet[f'J{row + 2 + indent}'].number_format = f'"{currency}"#,##0.00'
            workSheet[f'K{row + 2 + indent}'] = f'=ROUND(J{row + 2 + indent}*1.25, 2)'
            workSheet[f'K{row + 2 + indent}'].number_format = f'"{currency}"#,##0.00'
            workSheet[f'L{row + 2 + indent}'] = f'=K{row + 2 + indent}*E{row + 2 + indent}'
            workSheet[f'L{row + 2 + indent}'].number_format = f'"{currency}"#,##0.00'
            workSheet[f'M{row + 2 + indent}'] = f'=L{row + 2 + indent}*1.2'
            workSheet[f'M{row + 2 + indent}'].number_format = f'"{currency}"#,##0.00'
            workSheet[f'N{row + 2 + indent}'] = dataTable[row][6]
            workSheet[f'O{row + 2 + indent}'] = dataTable[row][7]
        
        workSheet[f'K{len(dataTable) + 2 + indent}'] = f'ИТОГО:'
        workSheet[f'L{len(dataTable) + 2 + indent}'] = f'=SUM(L{2 + indent}:L{len(dataTable) + 1 + indent})'
        workSheet[f'L{len(dataTable) + 2 + indent}'].number_format = f'"{currency}"#,##0.00'
        workSheet[f'M{len(dataTable) + 2 + indent}'] = f'=SUM(M{2 + indent}:M{len(dataTable) + 1 + indent})'
        workSheet[f'M{len(dataTable) + 2 + indent}'].number_format = f'"{currency}"#,##0.00'
        
        workSheet[f'K{len(dataTable) + 5 + indent}'] = f'Прибыль'
        workSheet[f'K{len(dataTable) + 6 + indent}'] = f'Прибыль %'
        workSheet[f'L{len(dataTable) + 5 + indent}'] = f'=L{len(dataTable) + 2 + indent}-I{len(dataTable) + 2 + indent}'
        workSheet[f'L{len(dataTable) + 5 + indent}'].number_format = f'"{currency}"#,##0.00'
        workSheet[f'L{len(dataTable) + 6 + indent}'] = f'=L{len(dataTable) + 5 + indent}/I{len(dataTable) + 2 + indent}'
        workSheet[f'L{len(dataTable) + 6 + indent}'].number_format = f'0%'
        
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        for row in workSheet.iter_rows():
            for cell in row:
                if self.cell_has_data(cell):
                    cell.border = border
                    cell.alignment = Alignment(horizontal='center', vertical='center')
        
        workSheet.move_range(f"A1:O1", rows=indent)
        
        try:
            
            Tools.write_log("creating Excel File...")
            Tools.write_log(f"Excel path to save: {newFilePath}")
            newFilePath = self.save_with_number(newFilePath)
            Tools.write_log(f"Final path to save: {newFilePath}")
            wb.save(newFilePath)
        except Exception as e:
            Tools.write_log(f"Unnable to save Excel: {e}")
            print(e)
        
    def cell_has_data(self, cell):
        if cell.value is not None and cell.value != "":
                return True
        return False
    
    def save_with_number(self, file_path):
        directory, filename = os.path.split(file_path)
        name, ext = os.path.splitext(filename)
        
        if not os.path.exists(file_path):
            return file_path
        
        counter = 1
        while True:
            new_filename = f"{name}({counter}){ext}"
            new_filepath = os.path.join(directory, new_filename)
            
            if not os.path.exists(new_filepath):
                return new_filepath
            
            counter += 1