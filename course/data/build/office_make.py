"""
Строит «эталонный» файл, который удовлетворяет списку проверок задания.
Нужен только при сборке курса: так мы убеждаемся, что каждое практическое
задание выполнимо, а пустой файл его не проходит.
"""
from __future__ import annotations

import io
import re

import docx
import openpyxl
import pptx
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches

PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c63f8cfc0f01f0005000201a2dd8c6e0000000049454e44ae426082"
)


def _field(paragraph, instr):
    run = paragraph.add_run()
    for kind, text in (("begin", None), (None, instr), ("separate", None), (None, "1"), ("end", None)):
        if kind:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), kind)
        elif text == instr:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = instr
        else:
            el = OxmlElement("w:t")
            el.text = text
        run._r.append(el)


def make_word(checks) -> bytes:
    d = docx.Document()
    filler = "Это пример абзаца с достаточным количеством слов для проверки документа ученика."

    def para(text, style=None):
        for p in d.paragraphs:
            if p.text == text:
                return p
        return d.add_paragraph(text, style=style)

    need_words = max([c.get("min", 0) for c in checks if c["t"] == "words"] + [0])
    need_paras = max([c.get("min", 0) for c in checks if c["t"] == "paragraphs"] + [0])
    for c in checks:
        t = c["t"]
        text = c.get("text") or "Пример текста"
        if t == "heading":
            d.add_heading(c.get("text") or "Заголовок", level=c.get("level", 1))
        elif t == "headings":
            for i in range(c["min"]):
                d.add_heading(f"Раздел {i + 1}", level=c.get("level", 1))
                d.add_paragraph(filler)
        elif t == "text":
            para(c["value"])
        elif t == "table_text":
            tb = d.tables[0] if d.tables else d.add_table(rows=3, cols=3)
            empty = next(x for row in tb.rows for x in row.cells if not x.text)
            empty.text = c["value"]
        elif t in ("bold", "italic", "underline", "color", "highlight", "font_size", "font"):
            p = para(text)
            for r in p.runs:
                if t == "bold": r.bold = True
                if t == "italic": r.italic = True
                if t == "underline": r.underline = True
                if t == "color": r.font.color.rgb = RGBColor(0xD9, 0x48, 0x0F)
                if t == "highlight": r.font.highlight_color = WD_COLOR_INDEX.YELLOW
                if t == "font_size": r.font.size = Pt(c["min"])
                if t == "font": r.font.name = c["name"]
        elif t == "align":
            p = para(text)
            p.alignment = {"center": WD_ALIGN_PARAGRAPH.CENTER, "right": WD_ALIGN_PARAGRAPH.RIGHT,
                           "justify": WD_ALIGN_PARAGRAPH.JUSTIFY, "left": WD_ALIGN_PARAGRAPH.LEFT}[c["value"]]
        elif t == "list":
            style = "List Number" if c.get("kind") == "number" else "List Bullet"
            for i in range(c["min"]):
                d.add_paragraph(f"Пункт {i + 1}", style=style)
        elif t == "table":
            d.add_table(rows=c.get("rows", 2), cols=c.get("cols", 2))
        elif t == "image":
            for _ in range(c.get("min", 1)):
                d.add_picture(io.BytesIO(PNG))
        elif t == "landscape":
            s = d.sections[0]
            s.orientation = WD_ORIENT.LANDSCAPE
            s.page_width, s.page_height = s.page_height, s.page_width
        elif t == "header":
            d.sections[0].header.paragraphs[0].text = c["value"]
        elif t == "footer":
            d.sections[0].footer.paragraphs[0].text = c["value"]
        elif t == "page_numbers":
            _field(d.sections[0].footer.paragraphs[0], "PAGE")
        elif t == "toc":
            _field(d.add_paragraph(), 'TOC \\o "1-3" \\h \\z \\u')
        elif t == "page_break":
            d.add_page_break()
        elif t == "columns":
            cols = d.sections[0]._sectPr.find(qn("w:cols"))
            if cols is None:
                cols = OxmlElement("w:cols")
                d.sections[0]._sectPr.append(cols)
            cols.set(qn("w:num"), str(c.get("min", 2)))
        elif t == "hyperlink":
            p = d.add_paragraph()
            h = OxmlElement("w:hyperlink")
            r = OxmlElement("w:r"); tt = OxmlElement("w:t"); tt.text = "ссылка"; r.append(tt); h.append(r)
            p._p.append(h)
        elif t == "footnote":
            pass  # сноски собираем ниже, вручную в zip
        elif t == "shape":
            p = d.add_paragraph()
            p._p.append(OxmlElement("w:r"))
            p._p[-1].append(_vml_rect())
    body_n = need_paras + 2
    for _ in range(body_n):
        d.add_paragraph(filler)
    while len(" ".join(p.text for p in d.paragraphs).split()) < need_words:
        d.add_paragraph(filler)
    for c in checks:
        if c["t"] == "line_spacing":
            for p in d.paragraphs:
                p.paragraph_format.line_spacing = c["min"]
        if c["t"] == "align_all":
            for p in d.paragraphs:
                if p.alignment is None:
                    p.alignment = (WD_ALIGN_PARAGRAPH.JUSTIFY if c["value"] == "justify"
                                   else WD_ALIGN_PARAGRAPH.CENTER)
        if c["t"] == "indent":
            for p in d.paragraphs:
                p.paragraph_format.first_line_indent = Pt(28)
    out = io.BytesIO()
    d.save(out)
    data = out.getvalue()
    if any(c["t"] == "footnote" for c in checks):
        data = _add_footnote(data)
    return data


def _vml_rect():
    from lxml import etree
    el = OxmlElement("w:pict")
    el.append(etree.Element("{urn:schemas-microsoft-com:vml}rect", nsmap={"v": "urn:schemas-microsoft-com:vml"}))
    return el


def _add_footnote(data: bytes) -> bytes:
    import zipfile
    src = zipfile.ZipFile(io.BytesIO(data))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            dst.writestr(item, src.read(item.filename))
        dst.writestr("word/footnotes.xml",
                     '<?xml version="1.0" encoding="UTF-8"?><w:footnotes xmlns:w="http://schemas.openxmlformats.org/'
                     'wordprocessingml/2006/main"><w:footnote w:type="separator" w:id="-1"/><w:footnote w:id="1">'
                     '<w:p><w:r><w:t>Сноска</w:t></w:r></w:p></w:footnote></w:footnotes>')
    return out.getvalue()


def make_excel(checks) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    names = [c["value"][:31] for c in checks if c["t"] == "sheet_name"]
    if names:
        ws.title = names[0]
        for n in names[1:]:
            wb.create_sheet(n)
    for c in checks:
        t = c["t"]
        ref = c.get("ref")
        if t == "cell":
            ws[ref] = c["value"]
        elif t == "formula":
            funcs = c.get("funcs") or ["SUM"]
            inner = "$A$1" if c.get("abs") else "A1"
            f = "=" + "".join(fn + "(" for fn in funcs) + inner + ")" * len(funcs)
            ws[ref] = f
        elif t == "formulas":
            func = c.get("func") or "SUM"
            for row in ws[c["range"]]:
                for x in row:
                    if not (isinstance(x.value, str) and x.value.startswith("=")):
                        x.value = f"={func}(A1)"
        elif t == "filled":
            for row in ws[c["range"]]:
                for x in row:
                    if x.value is None:
                        x.value = 1
        elif t == "text":
            ws.cell(row=ws.max_row + 1, column=8, value=c["value"])
        elif t == "bold":
            for row in ws[ref] if ":" in ref else [[ws[ref]]]:
                for x in row:
                    x.font = Font(bold=True)
        elif t == "fill":
            for row in ws[ref] if ":" in ref else [[ws[ref]]]:
                for x in row:
                    x.fill = PatternFill("solid", fgColor="FFD166")
        elif t == "align":
            for row in ws[ref] if ":" in ref else [[ws[ref]]]:
                for x in row:
                    x.alignment = Alignment(horizontal="center", wrap_text=x.alignment.wrap_text)
        elif t == "wrap":
            for row in ws[ref] if ":" in ref else [[ws[ref]]]:
                for x in row:
                    x.alignment = Alignment(wrap_text=True, horizontal=x.alignment.horizontal)
        elif t == "number_format":
            fmt = {"%": "0%", "0.00": "0.00", "₸": '#,##0 "₸"'}.get(c["contains"], c["contains"])
            for row in ws[ref] if ":" in ref else [[ws[ref]]]:
                for x in row:
                    x.number_format = fmt
                    if x.value is None:
                        x.value = 1
        elif t == "date":
            import datetime as _dt
            for row in ws[ref] if ":" in ref else [[ws[ref]]]:
                for x in row:
                    x.value = _dt.date(2026, 9, 1)
        elif t == "border":
            side = Side(style="thin")
            for row in ws[c["range"]]:
                for x in row:
                    x.border = Border(left=side, right=side, top=side, bottom=side)
        elif t == "merged":
            ws.merge_cells(c["range"])
        elif t == "col_width":
            ws.column_dimensions[c["col"]].width = c["min"] + 2
        elif t == "sheets":
            while len(wb.sheetnames) < c["min"]:
                wb.create_sheet(f"Лист{len(wb.sheetnames) + 1}")
        elif t == "chart":
            for i in range(1, 5):
                ws.cell(row=20 + i, column=1, value=f"К{i}")
                ws.cell(row=20 + i, column=2, value=i * 3)
            ch = {"pie": PieChart, "line": LineChart}.get(c.get("kind"), BarChart)()
            ch.add_data(Reference(ws, min_col=2, min_row=21, max_row=24))
            ch.set_categories(Reference(ws, min_col=1, min_row=21, max_row=24))
            ws.add_chart(ch, "J2")
        elif t == "autofilter":
            ws.auto_filter.ref = "A1:D10"
        elif t == "freeze":
            ws.freeze_panes = "A2"
        elif t == "cond_format":
            ws.conditional_formatting.add("B2:B10", CellIsRule(operator="greaterThan", formula=["5"],
                                                               fill=PatternFill("solid", fgColor="A8DC98")))
        elif t == "validation":
            dv = DataValidation(type="whole", operator="between", formula1="1", formula2="5")
            ws.add_data_validation(dv)
            dv.add("C2:C10")
        elif t == "sorted":
            cells = [x for row in ws[c["range"]] for x in row]
            vals = list(range(1, len(cells) + 1))
            if c.get("desc"):
                vals.reverse()
            for x, v in zip(cells, vals):
                x.value = v
        elif t == "table_obj":
            ws2 = ws
            for r in range(30, 33):
                for col in range(1, 3):
                    ws2.cell(row=r, column=col, value=f"h{col}" if r == 30 else r)
            ws2.add_table(Table(displayName="Data1", ref="A30:B32"))
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def make_pptx(checks) -> bytes:
    prs = pptx.Presentation()
    need = max([c.get("min", 1) for c in checks if c["t"] == "slides"] +
               [c.get("slide", 1) for c in checks] + [1])
    for i in range(need):
        s = prs.slides.add_slide(prs.slide_layouts[1])
        s.shapes.title.text = f"Слайд {i + 1}"
    slides = list(prs.slides)
    for c in checks:
        t = c["t"]
        targets = [slides[c["slide"] - 1]] if c.get("slide") else slides[:1]
        for s in targets:
            if t == "title" and c.get("text"):
                s.shapes.title.text = c["text"]
            elif t == "text":
                tb = s.shapes.add_textbox(Inches(1), Inches(6), Inches(6), Inches(1))
                tb.text_frame.text = c["value"]
            elif t == "bullets":
                body = s.placeholders[1]
                body.text_frame.text = "Пункт 1"
                for k in range(2, c["min"] + 1):
                    body.text_frame.add_paragraph().text = f"Пункт {k}"
            elif t == "image":
                for _ in range(c.get("min", 1)):
                    s.shapes.add_picture(io.BytesIO(PNG), Inches(1), Inches(1))
            elif t == "table":
                s.shapes.add_table(2, 2, Inches(1), Inches(4), Inches(4), Inches(1))
            elif t == "chart":
                data = CategoryChartData()
                data.categories = ["А", "Б"]
                data.add_series("Ряд", (1, 2))
                s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(1), Inches(1), Inches(4), Inches(3), data)
            elif t == "smartart":
                gf = s.shapes.add_table(1, 1, Inches(1), Inches(1), Inches(1), Inches(1))
                gf._element.graphic.graphicData.set("uri", "http://schemas.openxmlformats.org/drawingml/2006/diagram")
            elif t == "shapes":
                for _ in range(c.get("min", 1)):
                    s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1), Inches(1), Inches(2), Inches(1))
            elif t == "animation":
                s._element.append(_el('<p:timing xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
                                      '<p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"/>'
                                      '</p:par></p:tnLst></p:timing>'))
            elif t == "notes":
                s.notes_slide.notes_text_frame.text = "Что сказать на этом слайде"
            elif t == "hyperlink":
                tb = s.shapes.add_textbox(Inches(1), Inches(5), Inches(4), Inches(1))
                run = tb.text_frame.paragraphs[0].add_run()
                run.text = "сайт"
                run.hyperlink.address = "https://example.com"
        if t == "transitions":
            for s in (slides if c.get("all") else slides[:c.get("min", 1)]):
                _add_transition(s)
        if t == "background":
            fill = slides[0].background.fill
            fill.solid()
            from pptx.dml.color import RGBColor as PRGB
            fill.fore_color.rgb = PRGB(0xFF, 0xD1, 0x66)
    out = io.BytesIO()
    prs.save(out)
    return out.getvalue()


def _el(xml):
    from lxml import etree
    return etree.fromstring(xml)


def _add_transition(slide):
    tr = _el('<p:transition xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:fade/></p:transition>')
    sld = slide._element
    timing = sld.find("{http://schemas.openxmlformats.org/presentationml/2006/main}timing")
    if timing is not None:
        timing.addprevious(tr)
    else:
        ext = sld.find("{http://schemas.openxmlformats.org/presentationml/2006/main}extLst")
        (ext.addprevious(tr) if ext is not None else sld.append(tr))


def make_blank(kind) -> bytes:
    return {"word": make_word, "excel": make_excel, "pptx": make_pptx}[kind]([])


def make_solution(kind, checks) -> bytes:
    return {"word": make_word, "excel": make_excel, "pptx": make_pptx}[kind](checks)


_ = re  # noqa: F841
