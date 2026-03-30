from __future__ import annotations

import re


class WebPageParser:
    @staticmethod
    def compact_text(value):
        return re.sub(r"\s+", " ", str(value or "")).strip()

    def extract_payload(self, html_text: str, *, current_url: str = ""):
        try:
            from lxml import html as lxml_html
            from lxml.etree import ParserError
        except ModuleNotFoundError as error:
            raise RuntimeError("Для парсинга веб-страницы требуется пакет lxml") from error

        try:
            document = lxml_html.fromstring(html_text)
        except (ParserError, ValueError) as error:
            raise ValueError("Не удалось разобрать HTML страницы") from error

        title = self.compact_text(document.xpath("string(//title)"))
        heading_nodes = document.xpath("//h1|//h2|//h3|//h4|//h5|//h6")
        headings = []
        for node in heading_nodes:
            text = self.compact_text(node.text_content())
            if text:
                headings.append(text)

        form_nodes = document.xpath("//form")
        forms = []
        for index, form in enumerate(form_nodes, start=1):
            fields = []
            for field in form.xpath(".//input|.//select|.//textarea"):
                field_name = self.compact_text(field.get("name") or field.get("id") or "—")
                field_type = self.compact_text(field.get("type") or field.tag or "field")
                fields.append({"name": field_name, "type": field_type})
            forms.append(
                {
                    "index": index,
                    "method": self.compact_text(form.get("method") or "GET").upper(),
                    "action": self.compact_text(form.get("action") or ""),
                    "fields": fields[:30],
                }
            )

        table_nodes = document.xpath("//table")
        tables = []
        for index, table in enumerate(table_nodes, start=1):
            row_nodes = table.xpath(".//tr")
            preview_rows = []
            for row_node in row_nodes[:8]:
                row_values = [
                    self.compact_text(cell.text_content()) for cell in row_node.xpath("./th|./td")
                ]
                if any(value for value in row_values):
                    preview_rows.append(row_values)
            tables.append(
                {
                    "index": index,
                    "rows_total": len(row_nodes),
                    "preview_rows": preview_rows[:5],
                }
            )

        link_nodes = document.xpath("//a[@href]")
        links_preview = []
        for link in link_nodes[:100]:
            href = self.compact_text(link.get("href"))
            if not href:
                continue
            text = self.compact_text(link.text_content()) or "—"
            links_preview.append({"text": text, "href": href})

        frame_nodes = document.xpath("//frame|//iframe")
        frames = []
        for frame in frame_nodes:
            src = self.compact_text(frame.get("src"))
            name = self.compact_text(frame.get("name") or frame.get("id") or "—")
            frames.append({"name": name, "src": src})

        return {
            "url": str(current_url or ""),
            "title": title,
            "html_size": len(html_text),
            "headings": headings[:30],
            "forms_count": len(form_nodes),
            "forms": forms,
            "tables_count": len(table_nodes),
            "tables": tables,
            "links_count": len(link_nodes),
            "links_preview": links_preview,
            "frames_count": len(frame_nodes),
            "frames": frames,
        }
