from docx import Document
from docx.shared import Pt
from decimal import Decimal, ROUND_HALF_UP
from tools import DatabaseTools as Tools
from tools import Tools as ExtraTools
from datetime import datetime, timedelta
import copy
import math
from openpyxl import load_workbook
from openpyxl.styles import Border, Side, Alignment
from config import Config
import shutil
import os

class createTextFile:
    def __init__(self, docxData):
        self.output_path = ""
        self.success = False
        self.error_message = ""

        Tools.write_log(f"test feature: {Config.settings['testFeature']}")
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

        for i in tableData:
            currency1, amount1 = Tools.parsePrice(i[6].replace(',', '.'))
            currency2, amount2 = Tools.parsePrice(i[7].replace(',', '.'))
            sum1 += float(amount1.replace(' ', ''))
            sum2 += float(amount2.replace(' ', ''))
            symbCurrency = currency1
            if int(i[8].split()[0]) > maxDays:
                maxDays = int(i[8].split()[0])
            if int(i[8].split()[0]) < minDays:
                minDays = int(i[8].split()[0])

        if minDays == maxDays:
            period = f'до {minDays}'
        else:
            period = f'от {minDays} до {maxDays}'

        currency = Config.currency[symbCurrency]

        if docxData[4]:
            TEMPLATE_PATH = Config.template_docx_path
        else:
            TEMPLATE_PATH = Config.template_docx_path_short

        OUTPUT_PATH = f"{Tools.resourcePath(Config.config['pathToSaveCP'])}/КП_{docxData[3]}_от_{datetime.now().strftime('%d.%m.%Y')}_.docx"
        self.output_path = OUTPUT_PATH

        VAT_RATE = Decimal("0.20")

        GENDER = {
            'мужской': ("ый", 'у'),
            'женский': ("ая", 'ой')
        }

        if Config.settings['testFeature']:
            post = Tools.formWord(customerData[8], 2)
            initials = f"{Tools.formWord(customerData[2], 2)} {customerData[1][0]}. {customerData[3][0]}."
        else:
            post = customerData[8]
            initials = f"{customerData[2]} {customerData[1][0]}. {customerData[3][0]}."

        PLACEHOLDERS = {
            "<<COMPANY>>": "ООО «АЛЬФА КАППА ИНЖИНИРИНГ»",
            "<<INN>>": "9731121825",
            "<<KPP>>": "772901001",
            "<<ADDRESS>>": "121471, Г.МОСКВА, УЛ., РЯБИНОВАЯ, Д.26 СТР.1, ПОМЕЩ.141",
            "<<SITE>>": "alphakappa.ru",
            "<<PHONE>>": "+7 (993) 338-47-22",
            "<<EMAIL>>": "admin@alphakappa.ru",

            "<<OUT_NUM>>": "9/19.01",
            "<<OUT_DATE>>": "19.01.2026",

            "<<TO_TITLE>>": "Директору",
            "<<CLIENT_COMPANY>>": "ООО Сусуман",
            "<<CLIENT_PERSON>>": "Иванов И. И.",

            "<<VALID_UNTIL>>": "29.01.2026",

            "<<SIGN_TITLE>>": "Гениральнай директор",
            "<<SIGN_NAME>>": "А. О. Кадыров",

            "{{num}}": f"{docxData[3]}",
            "{{date_f}}": f"{datetime.now().strftime('%d.%m')}",
            "{{now}}": f"{datetime.now().strftime('%d.%m.%Y')}",
            "{{post}}": post,
            "{{company}}": customerData[7],
            "{{initials}}": initials,

            "Уважаемая Иван Иваныч !": f"Уважаем{GENDER[customerData[10]][0]} {customerData[1]} {customerData[3]} !",
            "{{gender}}": f"{GENDER[customerData[10]][0]}",
            "{{name}}": f"{customerData[1]}",
            "{{surname}}": f"{customerData[3]}",
            "{{app_num}}": f"{extraData[0]}",

            "{{Total_wo}}": f"{Tools.num2text(sum2)}",
            "{{Currency}}": f"{currency[0]}",
            "{{Total_diff}}": f"{Tools.num2text(round(sum2 - sum1, 2))}",

            "{{Total_wo_text}}": f"({tool.decimal2text(sum1,int_units=currency[1],exp_units=currency[2])})",

            "{{Total_diff_text}}": f"({tool.decimal2text(sum2 - sum1,int_units=currency[1],exp_units=currency[2])})",

            "{{NDS}}": f"{Tools.load_json(Config.vars_path)['parameters']['1'][1]}",

            "{{Conditions}}": f"{customerData[9]}",
            "{{Garanty_period}}": f"{extraData[1]}",
            "{{MinDays}}": f"{period}",
            "{{Producer}}": f"{extraData[3]}",
            "{{Pay_period}}": f"{extraData[2]}",
            "{{Pay_cond}}": f"{docxData[5]}",
            "{{date_20days}}": f"{(datetime.now() + timedelta(days=10)).strftime('%d.%m.%Y')}"
        }

        ITEMS = [

        ]

        for item in tableData:
            ITEMS.append({"name": item[1],
                          "sku": item[2],
                          "unit": item[3],
                          "qty": item[4],
                          "price": Decimal(Tools.parsePrice(item[5])[1].replace(',', '.').replace(' ', '')),
                          "sum_wo": Decimal(Tools.parsePrice(item[6])[1].replace(',', '.').replace(' ', '')),
                          "sum_w": Decimal(Tools.parsePrice(item[7])[1].replace(',', '.').replace(' ', '')),
                          "days": item[8]})

        ROW_TOKENS = {
            "<<I>>": None,
            "<<Name>>": None,
            "<<SKU>>": None,
            "<<Unit>>": None,
            "<<Qty>>": None,
            "<<Price>>": None,
            "<<Sum_wo>>": None,
            "<<Sum_w>>": None,
        }

        if docxData[4]:
            ROW_TOKENS["<<Days>>"] = None

        TOTAL_TOKENS = {
            "<<TOTAL_WO>>": None,
            "<<TOTAL_W>>": None,
        }

        def _fmt_dec_comma(v: Decimal) -> str:
            x = v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return f"{x:.2f}".replace(".", ",")


        def fmt_money_with_symbol(v) -> str:
            return symbCurrency + _fmt_dec_comma(Decimal(str(v)))


        def fmt_money_no_symbol(v) -> str:
            return _fmt_dec_comma(Decimal(str(v)))


        def _estimate_table_visual_rows(items: list[dict]) -> int:
            # Word page layout недоступен в python-docx, поэтому оцениваем высоту
            # строки по самым "узким" колонкам (наименование/артикул/срок).
            if not items:
                return 0

            name_chars_per_line = 28 if docxData[4] else 34
            sku_chars_per_line = 22 if docxData[4] else 26
            days_chars_per_line = 10

            visual_rows = 0
            for it in items:
                name_lines = max(1, math.ceil(len(str(it.get("name", "")).strip()) / name_chars_per_line))
                sku_lines = max(1, math.ceil(len(str(it.get("sku", "")).strip()) / sku_chars_per_line))
                days_lines = 1
                if docxData[4]:
                    days_lines = max(1, math.ceil(len(str(it.get("days", "")).strip()) / days_chars_per_line))
                visual_rows += max(name_lines, sku_lines, days_lines)
            return visual_rows


        def _table_spans_multiple_pages(items: list[dict]) -> bool:
            # Эмпирическая емкость первой страницы с учетом текста до таблицы.
            capacity = 18 if docxData[4] else 14
            return _estimate_table_visual_rows(items) > capacity


        def _apply_top_indent_for_multipage_table(doc: Document, items: list[dict]) -> None:
            if not _table_spans_multiple_pages(items):
                return

            extra_top_indent_pt = 14
            for sec in doc.sections:
                current_margin = int(sec.top_margin or 0)
                sec.top_margin = current_margin + int(Pt(extra_top_indent_pt))


        def _replace_in_paragraph_runs(paragraph, mapping: dict[str, str]) -> bool:
            changed = False
            for r in paragraph.runs:
                for k, v in mapping.items():
                    if k in r.text:
                        r.text = r.text.replace(k, v)
                        changed = True
            return changed


        def _replace_in_paragraph_fallback_merge(paragraph, mapping: dict[str, str]) -> bool:
            if not paragraph.runs:
                return False

            full = "".join(r.text for r in paragraph.runs)
            new = full
            for k, v in mapping.items():
                if k in new:
                    new = new.replace(k, v)

            if new == full:
                return False

            paragraph.runs[0].text = new
            for r in paragraph.runs[1:]:
                r.text = ""
            return True


        def replace_placeholders_everywhere(doc: Document, mapping: dict[str, str]) -> None:
            def handle_paragraph(p):
                changed = _replace_in_paragraph_runs(p, mapping)
                if not changed:
                    _replace_in_paragraph_fallback_merge(p, mapping)

            for p in doc.paragraphs:
                handle_paragraph(p)

            for t in doc.tables:
                for row in t.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            handle_paragraph(p)

            for sec in doc.sections:
                for p in sec.header.paragraphs:
                    handle_paragraph(p)
                for p in sec.footer.paragraphs:
                    handle_paragraph(p)


        def _set_cell_text_keep_style(cell, text: str) -> None:
            p = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
            if not p.runs:
                p.add_run(text)
            else:
                p.runs[0].text = text
                for r in p.runs[1:]:
                    r.text = ""
            for extra_p in cell.paragraphs[1:]:
                for r in extra_p.runs:
                    r.text = ""


        def _find_products_table(doc: Document):
            need = ["Наименование", "Каталожный товар", "Кол-во"]
            for t in doc.tables:
                if len(t.rows) == 0:
                    continue
                header = " | ".join(c.text for c in t.rows[0].cells)
                if all(x in header for x in need):
                    return t
            return doc.tables[1] if len(doc.tables) > 1 else None


        def _row_text_lower(row) -> str:
            return "|".join((c.text or "") for c in row.cells).lower()


        def _find_row_idx_by_token(table, token: str) -> int | None:
            tok = token.lower()
            for i, row in enumerate(table.rows):
                if tok in _row_text_lower(row):
                    return i
            return None

        def _find_header_row_idx(table) -> int:
            need = ["наименование", "каталожный", "кол-во"]
            for i, row in enumerate(table.rows):
                rt = _row_text_lower(row)
                if all(x in rt for x in need):
                    return i
            return 0

        def _find_total_row_idx(table) -> int:
            for i, row in enumerate(table.rows):
                for cell in row.cells:
                    if (cell.text or "").strip().lower() == "итого":
                        return i
            return len(table.rows) - 1

        def _fill_row_by_indices(row, idx: int, it: dict, sum_wo: Decimal, sum_w: Decimal):
            _set_cell_text_keep_style(row.cells[0], str(idx))
            _set_cell_text_keep_style(row.cells[1], it["name"])
            _set_cell_text_keep_style(row.cells[2], it["sku"])
            _set_cell_text_keep_style(row.cells[3], it["unit"])
            _set_cell_text_keep_style(row.cells[4], str(it["qty"]))
            _set_cell_text_keep_style(row.cells[5], Tools.formatPrice(_fmt_dec_comma(it["price"]), symbCurrency))
            _set_cell_text_keep_style(row.cells[6], Tools.formatPrice(_fmt_dec_comma(sum_wo), symbCurrency))
            _set_cell_text_keep_style(row.cells[7], Tools.formatPrice(_fmt_dec_comma(sum_w), symbCurrency))
            if docxData[4]:
                _set_cell_text_keep_style(row.cells[8], it["days"])


        def _fill_row_by_tokens(row, mapping: dict[str, str]):
            for cell in row.cells:
                for p in cell.paragraphs:
                    _replace_in_paragraph_runs(p, mapping)
                    _replace_in_paragraph_fallback_merge(p, mapping)


        def fill_products_table(doc: Document, items: list[dict]) -> tuple[Decimal, Decimal, Decimal]:
            table = _find_products_table(doc)
            if table is None:
                raise RuntimeError("Не нашёл таблицу товаров в документе.")

            header_idx = _find_header_row_idx(table)
            total_idx = _find_total_row_idx(table)

            template_idx = _find_row_idx_by_token(table, "<<Name>>")
            if template_idx is None:
                template_idx = _find_row_idx_by_token(table, "{{Name}}")

            if template_idx is None:
                template_idx = header_idx + 1
                if template_idx >= total_idx:
                    raise RuntimeError("В таблице нет строки-образца товара между заголовком и итогом.")

            template_tr = copy.deepcopy(table.rows[template_idx]._tr)

            for i in range(total_idx - 1, header_idx, -1):
                if i == template_idx:
                    continue
                table._tbl.remove(table.rows[i]._tr)

            total_idx = _find_total_row_idx(table)
            total_tr = table.rows[total_idx]._tr

            total_wo = Decimal("0.00")
            total_w = Decimal("0.00")

            template_row_text = _row_text_lower(table.rows[template_idx])
            use_tokens = ("<<Name>>" in template_row_text) or ("{{Name}}" in template_row_text)

            for n, it in enumerate(items, start=1):
                price = Decimal(str(it["price"]))
                qty = Decimal(str(it["qty"]))
                sum_wo = it['sum_wo']
                sum_w = it['sum_w']

                total_wo += sum_wo
                total_w += sum_w

                if n == 1:
                    row = table.rows[template_idx]
                else:
                    new_tr = copy.deepcopy(template_tr)
                    total_tr.addprevious(new_tr)
                    row = table.rows[_find_total_row_idx(table) - 1]

                if use_tokens:
                    row_map = {
                        "<<I>>": str(n),
                        "<<Name>>": it["name"],
                        "<<SKU>>": it["sku"],
                        "<<UNIT>>": it["unit"],
                        "<<QTY>>": str(it["qty"]),
                        "<<PRICE>>": Tools.num2text(fmt_money_with_symbol(price)),
                        "<<SUM_WO>>": currency[0] + _fmt_dec_comma(sum_wo),
                        "<<SUM_W>>": currency[0] + _fmt_dec_comma(sum_w),
                        "<<DAYS>>": it["days"],
                        "{{I}}": str(n),
                        "{{NAME}}": it["name"],
                        "{{SKU}}": it["sku"],
                        "{{UNIT}}": it["unit"],
                        "{{QTY}}": str(it["qty"]),
                        "{{PRICE}}": Tools.num2text(fmt_money_with_symbol(price)),
                        "{{SUM_WO}}": fmt_money_with_symbol(_fmt_dec_comma(sum_wo)),
                        "{{SUM_W}}": fmt_money_with_symbol(_fmt_dec_comma(sum_w)),
                    }
                    if docxData[4]:
                        row_map["{{DAYS}}"] = it["days"]
                    _fill_row_by_tokens(row, row_map)
                else:
                    _fill_row_by_indices(row, n, it, sum_wo, sum_w)

            total_row = table.rows[_find_total_row_idx(table)]
            total_row_text = _row_text_lower(total_row)
            if any(token in total_row_text for token in ("<<total_wo>>", "<<total_w>>", "{{total_wo}}", "{{total_w}}")):
                total_wo_text = Tools.formatPrice(_fmt_dec_comma(total_wo), symbCurrency)
                total_w_text = Tools.formatPrice(_fmt_dec_comma(total_w), symbCurrency)
                totals_map = {
                    "<<TOTAL_WO>>": total_wo_text,
                    "<<TOTAL_W>>": total_w_text,
                    "{{TOTAL_WO}}": total_wo_text,
                    "{{TOTAL_W}}": total_w_text,
                    "<<total_wo>>": total_wo_text,
                    "<<total_w>>": total_w_text,
                    "{{total_wo}}": total_wo_text,
                    "{{total_w}}": total_w_text,
                }
                _fill_row_by_tokens(total_row, totals_map)
            else:
                _set_cell_text_keep_style(total_row.cells[6], currency[0] + _fmt_dec_comma(total_wo))
                _set_cell_text_keep_style(total_row.cells[7], currency[0] + _fmt_dec_comma(total_w))

            vat_sum = (total_w - total_wo).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return total_wo, vat_sum, total_w


        def main():
            doc = Document(TEMPLATE_PATH)
            _apply_top_indent_for_multipage_table(doc, ITEMS)

            total_wo, vat_sum, total_w = fill_products_table(doc, ITEMS)
            mapping = dict(PLACEHOLDERS)
            mapping["<<TOTAL_WO_CNY>>"] = fmt_money_no_symbol(total_wo)
            mapping["<<VAT_CNY>>"] = fmt_money_no_symbol(round(vat_sum, 2))
            mapping["<<TOTAL_W_CNY>>"] = fmt_money_no_symbol(total_w)

            replace_placeholders_everywhere(doc, mapping)

            doc.save(OUTPUT_PATH)

        try:
            main()
            Tools.write_log("creating docx File...")
            Tools.write_log(f"saving docx to: {Tools.resourcePath(Config.config['pathToSaveCP'])}")
            self.success = True

        except Exception as e:
            Tools.write_log(f"Unnable to save Docx: {e}")
            self.error_message = str(e)

class createExcelFile:
    def __init__(self, data):
        self.output_path = ""
        self.success = False
        self.error_message = ""

        indent = int(Config.config['ExcelIndent'])
        request_number = str(data[4]).strip() if len(data) > 4 else str(Config.config.get("requestNumber", "")).strip()
        today_date = datetime.now().strftime('%d_%m_%Y')
        newFilePath = self.save_with_number(
            f"{Tools.resourcePath(Config.config['pathToSaveExcel'])}/Расчеты_{request_number}_{today_date}_.xlsx"
        )
        self.output_path = newFilePath
        shutil.copy2(Config.template_path, newFilePath)
        wb = load_workbook(newFilePath)
        workSheet = wb.active

        dataTable = data[0]
        params = data[1]
        for row in range(len(dataTable)):
            currency, unitPrice = Tools.parsePrice(dataTable[row][5])
            workSheet[f'A{row + 2 + indent}'] = int(dataTable[row][0])
            workSheet[f'B{row + 2 + indent}'] = dataTable[row][1]
            workSheet[f'C{row + 2 + indent}'] = dataTable[row][2]
            workSheet[f'D{row + 2 + indent}'] = dataTable[row][3]
            workSheet[f'E{row + 2 + indent}'] = int(dataTable[row][4])
            workSheet[f'F{row + 2 + indent}'] = float(unitPrice.replace(' ', '').replace(',', '.'))
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
        workSheet[f'H{len(dataTable) + 4 + indent}'] = f'=H{len(dataTable) + 3 + indent}/G{len(dataTable) + 2 + indent}'

        for row in range(len(dataTable)):
            workSheet[f'I{row + 2 + indent}'] = f'=H{row + 2 + indent}*{data[2]}'
            workSheet[f'I{row + 2 + indent}'].number_format = f'"{currency}"#,##0.00'
            workSheet[f'J{row + 2 + indent}'] = f'=I{row + 2 + indent}/E{row + 2 + indent}'
            workSheet[f'J{row + 2 + indent}'].number_format = f'"{currency}"#,##0.00'
            workSheet[f'K{row + 2 + indent}'] = f'=ROUND(J{row + 2 + indent}*{params[2]}, 2)'
            workSheet[f'K{row + 2 + indent}'].number_format = f'"{currency}"#,##0.00'
            workSheet[f'L{row + 2 + indent}'] = f'=K{row + 2 + indent}*E{row + 2 + indent}'
            workSheet[f'L{row + 2 + indent}'].number_format = f'"{currency}"#,##0.00'
            workSheet[f'M{row + 2 + indent}'] = f"=L{row + 2 + indent}*{1+(float(Tools.load_json(Config.vars_path)['parameters']['1'][1])/100)}"
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
            Tools.write_log(f"Final path to save: {newFilePath}")
            wb.save(newFilePath)
            self.success = True
        except Exception as e:
            Tools.write_log(f"Unnable to save Excel: {e}")
            self.error_message = str(e)

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
