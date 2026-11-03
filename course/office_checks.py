"""
Проверка файлов Word (.docx), Excel (.xlsx) и PowerPoint (.pptx), которые загружает ученик.

Каждое задание хранит список проверок вида {"t": "bold", "text": "Привет"}.
check_file() открывает файл и возвращает по каждой проверке {"ok": bool, "msg": str}
с понятным ребёнку текстом на русском или казахском.
"""
from __future__ import annotations

import io
import re
import zipfile

EXT = {"word": ".docx", "excel": ".xlsx", "pptx": ".pptx"}
MAX_SIZE = 10 * 1024 * 1024


def norm(s) -> str:
    s = "" if s is None else str(s)
    return re.sub(r"\s+", " ", s.replace("ё", "е").replace("Ё", "Е")).strip().casefold()


def relaxed(s) -> str:
    """Для текста, который набирает ученик: кроме регистра и ё/е, не важны и пробелы."""
    return re.sub(r"\s+", "", norm(s))


def has(text, needle) -> bool:
    return relaxed(needle) in relaxed(text)


def q(s):
    return f"«{s}»"


def L(lang, ru, kk):
    return kk if lang == "kk" else ru


# ---------------------------------------------------------------- Word

def _word_paragraphs(doc):
    ps = list(doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                ps.extend(cell.paragraphs)
    return ps


def _style_chain(style):
    while style is not None:
        yield style
        style = style.base_style


def _run_prop(run, para, prop):
    """Значение bold/italic/underline/size/name с учётом стилей символа и абзаца."""
    v = getattr(run.font, prop)
    if v is not None:
        return v
    if run.style is not None:
        for st in _style_chain(run.style):
            v = getattr(st.font, prop, None)
            if v is not None:
                return v
    for st in _style_chain(para.style):
        v = getattr(st.font, prop, None)
        if v is not None:
            return v
    return None


def _paras_with(doc, text):
    return [p for p in _word_paragraphs(doc) if (has(p.text, text) if text else p.text.strip())]


def _runs_with_prop(doc, text, prop, test=bool):
    """Есть ли абзац, где текст text целиком набран прогонами со свойством prop."""
    for p in _paras_with(doc, text):
        good = "".join(r.text for r in p.runs if test(_run_prop(r, p, prop)))
        if text and has(good, text):
            return True
        if not text and good.strip():
            return True
    return False


def _heading_level(p):
    for st in _style_chain(p.style):
        name = (st.name or "").lower()
        m = re.match(r"(heading|заголовок|тақырып)\s*(\d)", name)
        if m:
            return int(m.group(2))
        if name == "title" or name == "название":
            return 0
    ol = p._p.xpath("./w:pPr/w:outlineLvl/@w:val")
    if ol:
        return int(ol[0]) + 1
    return None


def _alignment(p):
    a = p.paragraph_format.alignment
    if a is None:
        for st in _style_chain(p.style):
            a = st.paragraph_format.alignment
            if a is not None:
                break
    return {None: "left", 0: "left", 1: "center", 2: "right", 3: "justify", 4: "justify",
            5: "justify", 7: "justify", 8: "justify", 9: "justify"}.get(int(a) if a is not None else None, "left")


def _list_kind(doc, p):
    """'bullet', 'number' или None."""
    num = p._p.xpath("./w:pPr/w:numPr/w:numId/@w:val")
    ilvl = p._p.xpath("./w:pPr/w:numPr/w:ilvl/@w:val")
    if not num:
        for st in _style_chain(p.style):
            num = st.element.xpath("./w:pPr/w:numPr/w:numId/@w:val")
            if num:
                break
            name = (st.name or "").lower()
            if "list bullet" in name or "маркир" in name:
                return "bullet"
            if "list number" in name or "нумер" in name:
                return "number"
    if not num or num[0] == "0":
        return None
    try:
        numbering = doc.part.numbering_part.element
    except Exception:  # noqa: BLE001
        return "number"
    lvl = ilvl[0] if ilvl else "0"
    abs_id = numbering.xpath(f'./w:num[@w:numId="{num[0]}"]/w:abstractNumId/@w:val')
    if not abs_id:
        return "number"
    fmt = numbering.xpath(f'./w:abstractNum[@w:abstractNumId="{abs_id[0]}"]/w:lvl[@w:ilvl="{lvl}"]/w:numFmt/@w:val')
    return "bullet" if fmt and fmt[0] == "bullet" else "number"


def _line_spacing(p):
    v = p.paragraph_format.line_spacing
    if v is None:
        for st in _style_chain(p.style):
            v = st.paragraph_format.line_spacing
            if v is not None:
                break
    if v is None:
        return 1.0
    if isinstance(v, float):
        return v
    return v.pt / 12.0  # точное значение в пунктах - пересчитываем примерно


def check_word(doc, z, c, lang):
    t = c["t"]
    text = c.get("text")
    if t == "text":
        body = "\n".join(p.text for p in _word_paragraphs(doc))
        return has(body, c["value"]), L(lang, f"В документе есть текст {q(c['value'])}", f"Құжатта {q(c['value'])} мәтіні бар")
    if t == "heading":
        lvl = c.get("level", 1)
        ok = any(_heading_level(p) == lvl and (not text or has(p.text, text)) and p.text.strip()
                 for p in doc.paragraphs)
        what = f" {q(text)}" if text else ""
        return ok, L(lang, f"Заголовок{what} оформлен стилем «Заголовок {lvl}»",
                     f"Тақырып{what} «Заголовок {lvl}» стилімен безендірілген")
    if t == "headings":
        n = sum(1 for p in doc.paragraphs if p.text.strip() and _heading_level(p) == c.get("level", 1))
        return n >= c["min"], L(lang, f"Заголовков уровня {c.get('level', 1)}: не меньше {c['min']} (сейчас {n})",
                                f"{c.get('level', 1)}-деңгейлі тақырыптар: кемінде {c['min']} (қазір {n})")
    if t in ("bold", "italic", "underline"):
        names = {"bold": ("жирным", "жуан"), "italic": ("курсивом", "көлбеу"), "underline": ("с подчёркиванием", "асты сызылған")}
        ok = _runs_with_prop(doc, text, t)
        ru, kk = names[t]
        return ok, L(lang, f"Текст {q(text)} выделен {ru}" if t != "underline" else f"Текст {q(text)} набран {ru}",
                     f"{q(text)} мәтіні {kk} қаріппен жазылған")
    if t == "align":
        names = {"center": ("по центру", "ортасына"), "right": ("по правому краю", "оң жаққа"),
                 "justify": ("по ширине", "ені бойынша"), "left": ("по левому краю", "сол жаққа")}
        ok = any(_alignment(p) == c["value"] for p in _paras_with(doc, text))
        ru, kk = names[c["value"]]
        what = q(text) if text else L(lang, "текста", "мәтін")
        return ok, L(lang, f"Выравнивание {what} - {ru}", f"{what} {kk} тураланған")
    if t == "align_all":
        ps = [p for p in doc.paragraphs if p.text.strip() and _heading_level(p) is None]
        ok = bool(ps) and sum(_alignment(p) == c["value"] for p in ps) >= 0.8 * len(ps)
        names = {"justify": ("по ширине", "ені бойынша"), "center": ("по центру", "ортасына")}
        ru, kk = names[c["value"]]
        return ok, L(lang, f"Основной текст выровнен {ru}", f"Негізгі мәтін {kk} тураланған")
    if t == "font_size":
        ok = False
        for p in _paras_with(doc, text):
            sizes = [_run_prop(r, p, "size") for r in p.runs if r.text.strip()]
            sizes = [s.pt if s is not None else 11 for s in sizes]
            if sizes and min(sizes) >= c["min"] and max(sizes) <= c.get("max", 999):
                ok = True
        what = q(text) if text else L(lang, "текста", "мәтін")
        return ok, L(lang, f"Размер шрифта {what} - не меньше {c['min']} пт", f"{what} қаріп өлшемі - кемінде {c['min']} пт")
    if t == "font":
        want = norm(c["name"])
        ok = False
        for p in _paras_with(doc, text):
            names = [norm(_run_prop(r, p, "name")) for r in p.runs if r.text.strip()]
            if names and all(n == want for n in names):
                ok = True
        what = q(text) if text else L(lang, "текста", "мәтін")
        return ok, L(lang, f"Шрифт {what} - {c['name']}", f"{what} қарпі - {c['name']}")
    if t == "color":
        def colored(run):
            col = run.font.color
            return col is not None and ((col.type is not None and col.rgb not in (None,) and str(col.rgb) != "000000")
                                        or col.theme_color is not None)
        ok = any(any(colored(r) for r in p.runs if r.text.strip()) for p in _paras_with(doc, text))
        return ok, L(lang, f"Текст {q(text)} окрашен в цвет", f"{q(text)} мәтіні түске боялған")
    if t == "highlight":
        ok = any(any(r.font.highlight_color is not None for r in p.runs if r.text.strip()) for p in _paras_with(doc, text))
        return ok, L(lang, f"Текст {q(text)} выделен маркером", f"{q(text)} мәтіні маркермен белгіленген")
    if t == "list":
        kind = c.get("kind")
        n = sum(1 for p in _word_paragraphs(doc) if p.text.strip() and (_list_kind(doc, p) == kind if kind else _list_kind(doc, p)))
        names = {"bullet": ("маркированном", "маркерленген"), "number": ("нумерованном", "нөмірленген"), None: ("", "")}
        ru, kk = names[kind]
        return n >= c["min"], L(lang, f"В {ru} списке не меньше {c['min']} пунктов (сейчас {n})".replace("В  ", "В "),
                                f"{kk} тізімде кемінде {c['min']} тармақ (қазір {n})".strip())
    if t == "table":
        ok = any(len(tb.rows) >= c.get("rows", 1) and len(tb.columns) >= c.get("cols", 1) for tb in doc.tables)
        return ok, L(lang, f"Есть таблица не меньше {c.get('rows', 1)}×{c.get('cols', 1)} (строк × столбцов)",
                     f"Кемінде {c.get('rows', 1)}×{c.get('cols', 1)} кесте бар (жол × баған)")
    if t == "table_text":
        cells = [cell.text for tb in doc.tables for row in tb.rows for cell in row.cells]
        return any(has(x, c["value"]) for x in cells), L(lang, f"В таблице есть {q(c['value'])}", f"Кестеде {q(c['value'])} бар")
    if t == "image":
        n = len(doc.element.body.xpath(".//pic:pic"))
        return n >= c.get("min", 1), L(lang, f"Вставлено картинок: не меньше {c.get('min', 1)} (сейчас {n})",
                                       f"Кірістірілген суреттер: кемінде {c.get('min', 1)} (қазір {n})")
    if t == "paragraphs":
        n = sum(1 for p in doc.paragraphs if p.text.strip())
        return n >= c["min"], L(lang, f"Абзацев с текстом: не меньше {c['min']} (сейчас {n})",
                                f"Мәтіні бар абзацтар: кемінде {c['min']} (қазір {n})")
    if t == "words":
        n = len(" ".join(p.text for p in _word_paragraphs(doc)).split())
        return n >= c["min"], L(lang, f"Слов в документе: не меньше {c['min']} (сейчас {n})",
                                f"Құжаттағы сөздер: кемінде {c['min']} (қазір {n})")
    if t == "landscape":
        s = doc.sections[0]
        ok = s.page_width is not None and s.page_height is not None and s.page_width > s.page_height
        return ok, L(lang, "Ориентация страницы - альбомная", "Бет бағдары - альбомдық")
    if t in ("header", "footer"):
        part = [s.header if t == "header" else s.footer for s in doc.sections]
        body = "\n".join(p.text for h in part for p in h.paragraphs)
        ru = "верхнем" if t == "header" else "нижнем"
        kk = "жоғарғы" if t == "header" else "төменгі"
        return has(body, c["value"]), L(lang, f"В {ru} колонтитуле есть {q(c['value'])}", f"{kk} колонтитулда {q(c['value'])} бар")
    if t == "page_numbers":
        ok = any(re.search(rb"PAGE", z.read(n)) for n in z.namelist() if re.match(r"word/(footer|header)\d*\.xml", n))
        return ok, L(lang, "На страницах есть номера (Вставка → Номер страницы)", "Беттерде нөмір бар (Вставка → Номер страницы)")
    if t == "line_spacing":
        ps = [p for p in doc.paragraphs if p.text.strip() and _heading_level(p) is None]
        ok = bool(ps) and sum(_line_spacing(p) >= c["min"] - 0.01 for p in ps) >= 0.8 * len(ps)
        return ok, L(lang, f"Междустрочный интервал - не меньше {c['min']}", f"Жол аралығы - кемінде {c['min']}")
    if t == "indent":
        ok = any((p.paragraph_format.first_line_indent or 0) > 0 or
                 any((st.paragraph_format.first_line_indent or 0) > 0 for st in _style_chain(p.style))
                 for p in doc.paragraphs if p.text.strip())
        return ok, L(lang, "У абзацев есть красная строка (отступ первой строки)", "Абзацтарда қызыл жол бар (бірінші жолдың шегінісі)")
    if t == "toc":
        xml = z.read("word/document.xml")
        ok = bool(re.search(rb"TOC \\", xml) or b"Table of Contents" in xml or re.search(rb"instrText[^>]*>\s*TOC", xml))
        return ok, L(lang, "Вставлено автоматическое оглавление (Ссылки → Оглавление)", "Автоматты мазмұн кірістірілген (Ссылки → Оглавление)")
    if t == "page_break":
        xml = z.read("word/document.xml")
        ok = b'w:type="page"' in xml or b"pageBreakBefore" in xml or len(doc.sections) > 1
        return ok, L(lang, "Есть разрыв страницы (Ctrl + Enter)", "Бет үзілімі бар (Ctrl + Enter)")
    if t == "columns":
        cols = doc.element.body.xpath(".//w:sectPr/w:cols/@w:num")
        ok = any(int(x) >= c.get("min", 2) for x in cols)
        return ok, L(lang, f"Текст разбит на колонки: не меньше {c.get('min', 2)}", f"Мәтін бағандарға бөлінген: кемінде {c.get('min', 2)}")
    if t == "hyperlink":
        ok = b"<w:hyperlink" in z.read("word/document.xml")
        return ok, L(lang, "В документе есть гиперссылка", "Құжатта гиперсілтеме бар")
    if t == "footnote":
        ok = "word/footnotes.xml" in z.namelist() and len(re.findall(rb"<w:footnote\b(?![^>]*w:type)[^>]*>", z.read("word/footnotes.xml"))) >= 1
        return ok, L(lang, "В документе есть сноска (Ссылки → Вставить сноску)", "Құжатта сілтеме бар (Ссылки → Вставить сноску)")
    if t == "shape":
        xml = z.read("word/document.xml")
        ok = b"<wps:wsp" in xml or b"<v:shape" in xml or b"<v:rect" in xml or b"<v:oval" in xml
        return ok, L(lang, "Вставлена фигура (Вставка → Фигуры)", "Пішін кірістірілген (Вставка → Фигуры)")
    raise ValueError(f"неизвестная проверка Word: {t}")


# ---------------------------------------------------------------- Excel

def _num(v):
    try:
        return float(str(v).replace(",", ".").replace(" ", ""))
    except (TypeError, ValueError):
        return None


def _same(a, b) -> bool:
    na, nb = _num(a), _num(b)
    if na is not None and nb is not None:
        return abs(na - nb) <= max(0.01, abs(nb) * 1e-6)
    return relaxed(a) == relaxed(b)


RU_FUNCS = {"SUM": "СУММ", "AVERAGE": "СРЗНАЧ", "MIN": "МИН", "MAX": "МАКС", "IF": "ЕСЛИ", "COUNT": "СЧЁТ",
            "COUNTIF": "СЧЁТЕСЛИ", "SUMIF": "СУММЕСЛИ", "ROUND": "ОКРУГЛ", "COUNTA": "СЧЁТЗ"}


def fname(f):
    return f"{RU_FUNCS[f]} ({f})" if f in RU_FUNCS else f


def _cells(ws, rng):
    for row in ws[rng] if ":" in rng else [[ws[rng]]]:
        yield from row


def check_excel(wb, wbv, z, c, lang):
    t = c["t"]
    ws = wb[c["sheet"]] if c.get("sheet") and c["sheet"] in wb.sheetnames else wb.worksheets[0]
    wsv = wbv[ws.title]
    ref = c.get("ref")
    if t == "cell":
        v = ws[ref].value
        if isinstance(v, str) and v.startswith("="):
            v = wsv[ref].value
            if v is None:  # файл без сохранённых значений формул
                return True, L(lang, f"В ячейке {ref} - {c['value']}", f"{ref} ұяшығында - {c['value']}")
        return _same(v, c["value"]), L(lang, f"В ячейке {ref} - {c['value']}", f"{ref} ұяшығында - {c['value']}")
    if t == "formula":
        v = ws[ref].value
        ok = isinstance(v, str) and v.startswith("=")
        funcs = [f.upper() for f in c.get("funcs", [])]
        if ok and funcs:
            ok = all(f + "(" in v.upper().replace(" ", "") for f in funcs)
        if ok and c.get("abs"):
            ok = "$" in v
        if ok and "value" in c and wsv[ref].value is not None:
            ok = _same(wsv[ref].value, c["value"])
        fn = (" " + L(lang, "с функцией ", "") + ", ".join(fname(f) for f in funcs)
              + L(lang, "", " функциясымен")) if funcs else ""
        msg = L(lang, f"В ячейке {ref} формула{fn}", f"{ref} ұяшығында формула{fn}")
        if "value" in c:
            msg += L(lang, f", результат {c['value']}", f", нәтижесі {c['value']}")
        if c.get("abs"):
            msg += L(lang, " (с абсолютной ссылкой $)", " ($ абсолютті сілтемемен)")
        return ok, msg
    if t == "formulas":
        cells = list(_cells(ws, c["range"]))
        func = c.get("func", "").upper()
        ok = all(isinstance(x.value, str) and x.value.startswith("=") and (not func or func + "(" in x.value.upper())
                 for x in cells)
        fn = f" {fname(func)}" if func else ""
        return ok, L(lang, f"Во всех ячейках {c['range']} есть формулы{fn}", f"{c['range']} ұяшықтарының бәрінде формула{fn} бар")
    if t == "filled":
        ok = all(x.value not in (None, "") for x in _cells(ws, c["range"]))
        return ok, L(lang, f"Ячейки {c['range']} заполнены", f"{c['range']} ұяшықтары толтырылған")
    if t == "text":
        ok = any(has(x.value, c["value"]) for row in ws.iter_rows() for x in row if x.value is not None)
        return ok, L(lang, f"В таблице есть {q(c['value'])}", f"Кестеде {q(c['value'])} бар")
    if t == "bold":
        ok = all(bool(x.font and x.font.b) for x in _cells(ws, ref))
        return ok, L(lang, f"Ячейки {ref} выделены жирным", f"{ref} ұяшықтары жуан қаріппен")
    if t == "fill":
        def filled(x):
            f = x.fill
            if not f or f.fill_type in (None, "none"):
                return False
            col = f.fgColor
            return not (col is not None and col.type == "rgb" and col.rgb in ("00000000", "FFFFFFFF"))
        ok = all(filled(x) for x in _cells(ws, ref))
        return ok, L(lang, f"Ячейки {ref} залиты цветом", f"{ref} ұяшықтары түспен құйылған")
    if t == "align":
        ok = all((x.alignment.horizontal or "") in (c["value"], "centerContinuous" if c["value"] == "center" else "-")
                 for x in _cells(ws, ref))
        return ok, L(lang, f"Ячейки {ref} выровнены по центру", f"{ref} ұяшықтары ортасына тураланған")
    if t == "wrap":
        ok = all(bool(x.alignment.wrap_text) for x in _cells(ws, ref))
        return ok, L(lang, f"В ячейках {ref} включён перенос текста", f"{ref} ұяшықтарында мәтінді тасымалдау қосулы")
    if t == "number_format":
        ok = all(c["contains"] in (x.number_format or "") for x in _cells(ws, ref))
        names = {"%": ("процентный", "пайыздық"), "0.00": ("с двумя знаками после запятой", "үтірден кейін екі таңбалы"),
                 "₸": ("денежный (₸)", "ақшалай (₸)")}
        ru, kk = names.get(c["contains"], (c["contains"], c["contains"]))
        return ok, L(lang, f"Формат ячеек {ref} - {ru}", f"{ref} ұяшықтарының пішімі - {kk}")
    if t == "date":
        import datetime as _dt
        ok = all(isinstance(x.value, (_dt.date, _dt.datetime)) for x in _cells(ws, ref))
        return ok, L(lang, f"В ячейках {ref} - даты (формат «Дата»)", f"{ref} ұяшықтарында - күндер («Дата» пішімі)")
    if t == "border":
        def bordered(x):
            b = x.border
            return any(getattr(b, side).style for side in ("left", "right", "top", "bottom"))
        ok = all(bordered(x) for x in _cells(ws, c["range"]))
        return ok, L(lang, f"У ячеек {c['range']} есть границы", f"{c['range']} ұяшықтарының шекаралары бар")
    if t == "merged":
        ok = any(str(m) == c["range"] or (c["range"].split(":")[0] in m and c["range"].split(":")[-1] in m)
                 for m in ws.merged_cells.ranges)
        return ok, L(lang, f"Ячейки {c['range']} объединены", f"{c['range']} ұяшықтары біріктірілген")
    if t == "col_width":
        w = ws.column_dimensions[c["col"]].width or 8.43
        return w >= c["min"], L(lang, f"Ширина столбца {c['col']} увеличена", f"{c['col']} бағанының ені үлкейтілген")
    if t == "sheets":
        n = len(wb.sheetnames)
        return n >= c["min"], L(lang, f"Листов в книге: не меньше {c['min']} (сейчас {n})", f"Кітаптағы парақтар: кемінде {c['min']} (қазір {n})")
    if t == "sheet_name":
        ok = any(relaxed(s) == relaxed(c["value"]) for s in wb.sheetnames)
        return ok, L(lang, f"Есть лист с названием {q(c['value'])}", f"{q(c['value'])} атты парақ бар")
    if t == "chart":
        charts = [n for n in z.namelist() if re.match(r"xl/charts/chart\d+\.xml$", n)]
        kind = c.get("kind")
        tags = {"bar": b"barChart", "pie": (b"pieChart", b"doughnutChart"), "line": b"lineChart"}
        if kind:
            want = tags[kind] if isinstance(tags[kind], tuple) else (tags[kind],)
            ok = any(any(tag in z.read(n) for tag in want) for n in charts)
        else:
            ok = bool(charts)
        names = {"bar": ("гистограмма", "гистограмма"), "pie": ("круговая диаграмма", "дөңгелек диаграмма"),
                 "line": ("график", "график"), None: ("диаграмма", "диаграмма")}
        ru, kk = names[kind]
        return ok, L(lang, f"Вставлена {ru}", f"{kk.capitalize()} кірістірілген")
    if t == "autofilter":
        return bool(ws.auto_filter and ws.auto_filter.ref), L(lang, "Включён фильтр (Данные → Фильтр)", "Сүзгі қосулы (Данные → Фильтр)")
    if t == "freeze":
        return bool(ws.freeze_panes), L(lang, "Закреплена верхняя строка (Вид → Закрепить области)", "Жоғарғы жол бекітілген (Вид → Закрепить области)")
    if t == "cond_format":
        n = sum(len(cf.rules) for cf in ws.conditional_formatting)
        return n >= 1, L(lang, "Есть условное форматирование", "Шартты пішімдеу бар")
    if t == "validation":
        n = len(ws.data_validations.dataValidation) if ws.data_validations else 0
        return n >= 1, L(lang, "Есть проверка данных (Данные → Проверка данных)", "Деректерді тексеру бар (Данные → Проверка данных)")
    if t == "sorted":
        vals = [x.value for x in _cells(ws, c["range"])]
        nums = [_num(v) for v in vals]
        keyed = nums if all(n is not None for n in nums) else [norm(v) for v in vals]
        ok = keyed == sorted(keyed, reverse=c.get("desc", False)) and len(set(map(str, keyed))) > 1
        how = L(lang, "по убыванию", "кему бойынша") if c.get("desc") else L(lang, "по возрастанию", "өсу бойынша")
        return ok, L(lang, f"Данные отсортированы {how} (столбец {c['range']})", f"Деректер {how} сұрыпталған ({c['range']} бағаны)")
    if t == "table_obj":
        return bool(ws.tables), L(lang, "Данные оформлены как таблица (Главная → Форматировать как таблицу)",
                                  "Деректер кесте ретінде безендірілген (Главная → Форматировать как таблицу)")
    raise ValueError(f"неизвестная проверка Excel: {t}")


# ---------------------------------------------------------------- PowerPoint

def _slide(prs, n):
    slides = list(prs.slides)
    return slides[n - 1] if 0 < n <= len(slides) else None


def _slide_text(slide):
    out = []
    for sh in slide.shapes:
        if sh.has_text_frame:
            out.append(sh.text_frame.text)
        if getattr(sh, "has_table", False) and sh.has_table:
            out.extend(cell.text for row in sh.table.rows for cell in row.cells)
    return "\n".join(out)


def _title(slide):
    try:
        t = slide.shapes.title
    except Exception:  # noqa: BLE001
        t = None
    return t.text_frame.text.strip() if t is not None and t.has_text_frame else ""


def _xml(el):
    from lxml import etree
    return etree.tostring(el)


def check_pptx(prs, z, c, lang):
    t = c["t"]
    slides = list(prs.slides)
    n = c.get("slide")
    where = (L(lang, f" на слайде {n}", f" {n}-слайдта")) if n else ""
    scope = [_slide(prs, n)] if n else slides
    scope = [s for s in scope if s is not None]
    if t == "slides":
        return len(slides) >= c["min"], L(lang, f"Слайдов в презентации: не меньше {c['min']} (сейчас {len(slides)})",
                                          f"Презентациядағы слайдтар: кемінде {c['min']} (қазір {len(slides)})")
    if t == "title":
        text = c.get("text")
        ok = any(_title(s) and (not text or has(_title(s), text)) for s in scope)
        what = f" {q(text)}" if text else ""
        return ok, L(lang, f"Заголовок{what}{where}", f"Тақырып{what}{where}")
    if t == "titles":
        ok = bool(slides) and all(_title(s) for s in slides)
        return ok, L(lang, "У каждого слайда есть заголовок", "Әр слайдтың тақырыбы бар")
    if t == "text":
        ok = any(has(_slide_text(s), c["value"]) for s in scope)
        return ok, L(lang, f"Текст {q(c['value'])}{where}", f"{q(c['value'])} мәтіні{where}")
    if t == "bullets":
        best = 0
        for s in scope:
            for sh in s.shapes:
                if sh.has_text_frame and not (sh.is_placeholder and sh.placeholder_format.type in (1, 3)):
                    best = max(best, sum(1 for p in sh.text_frame.paragraphs if "".join(r.text for r in p.runs).strip()))
        return best >= c["min"], L(lang, f"Список из {c['min']} пунктов{where}", f"{c['min']} тармақты тізім{where}")
    if t == "image":
        cnt = sum(len(s.shapes._spTree.xpath(".//p:pic")) for s in scope)
        return cnt >= c.get("min", 1), L(lang, f"Картинок{where}: не меньше {c.get('min', 1)} (сейчас {cnt})",
                                         f"Суреттер{where}: кемінде {c.get('min', 1)} (қазір {cnt})")
    if t == "table":
        ok = any(getattr(sh, "has_table", False) and sh.has_table for s in scope for sh in s.shapes)
        return ok, L(lang, f"Вставлена таблица{where}", f"Кесте кірістірілген{where}")
    if t == "chart":
        ok = any(getattr(sh, "has_chart", False) and sh.has_chart for s in scope for sh in s.shapes)
        return ok, L(lang, f"Вставлена диаграмма{where}", f"Диаграмма кірістірілген{where}")
    if t == "smartart":
        ok = any(b"/diagram" in _xml(sh._element) for s in scope for sh in s.shapes)
        return ok, L(lang, f"Вставлен рисунок SmartArt{where}", f"SmartArt суреті кірістірілген{where}")
    if t == "shapes":
        cnt = sum(1 for s in scope for sh in s.shapes if sh.shape_type == 1)  # MSO_SHAPE_TYPE.AUTO_SHAPE
        return cnt >= c.get("min", 1), L(lang, f"Фигур{where}: не меньше {c.get('min', 1)} (сейчас {cnt})",
                                         f"Пішіндер{where}: кемінде {c.get('min', 1)} (қазір {cnt})")
    if t == "transitions":
        cnt = sum(1 for s in slides if b"transition" in _xml(s._element))
        need = len(slides) if c.get("all") else c.get("min", 1)
        return cnt >= need and cnt > 0, L(lang, "Переходы добавлены " + ("ко всем слайдам" if c.get("all") else f"(слайдов с переходом: {cnt})"),
                                          "Ауысулар " + ("барлық слайдқа қосылған" if c.get("all") else f"қосылған (ауысуы бар слайдтар: {cnt})"))
    if t == "animation":
        cnt = sum(1 for s in scope if b"<p:par" in _xml(s._element) and b"timing" in _xml(s._element))
        return cnt >= 1, L(lang, f"Добавлена анимация{where}", f"Анимация қосылған{where}")
    if t == "notes":
        ok = any(s.has_notes_slide and s.notes_slide.notes_text_frame is not None and s.notes_slide.notes_text_frame.text.strip()
                 for s in scope)
        return ok, L(lang, f"Есть заметки докладчика{where}", f"Баяндамашы жазбалары бар{where}")
    if t == "hyperlink":
        ok = any(b"hlinkClick" in _xml(s._element) for s in scope)
        return ok, L(lang, f"Есть гиперссылка{where}", f"Гиперсілтеме бар{where}")
    if t == "background":
        ok = any(s._element.find(".//{http://schemas.openxmlformats.org/presentationml/2006/main}bg") is not None for s in slides)
        if not ok:
            for m in prs.slide_masters:
                bg = m._element.find(".//{http://schemas.openxmlformats.org/presentationml/2006/main}bgPr")
                if bg is not None:
                    ok = True
        return ok, L(lang, "Изменён фон слайдов (Конструктор → Формат фона)", "Слайдтар фоны өзгертілген (Конструктор → Формат фона)")
    raise ValueError(f"неизвестная проверка PowerPoint: {t}")


# ---------------------------------------------------------------- общий вход

def check_file(course_kind: str, data: bytes, checks: list, lang: str = "ru"):
    """Возвращает (results, error). results - список {"ok", "msg"}; error - текст, если файл не открылся."""
    bad = L(lang, f"Не получилось открыть файл. Сохрани его в формате {EXT[course_kind]} и загрузи ещё раз.",
            f"Файлды ашу мүмкін болмады. Оны {EXT[course_kind]} пішімінде сақтап, қайта жүкте.")
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        if course_kind == "word":
            import docx
            obj = docx.Document(io.BytesIO(data))
            fn = lambda c: check_word(obj, z, c, lang)  # noqa: E731
        elif course_kind == "excel":
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(data))
            wbv = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
            fn = lambda c: check_excel(wb, wbv, z, c, lang)  # noqa: E731
        else:
            import pptx
            obj = pptx.Presentation(io.BytesIO(data))
            fn = lambda c: check_pptx(obj, z, c, lang)  # noqa: E731
    except Exception:  # noqa: BLE001 - любой битый файл
        return [], bad
    results = []
    for c in checks:
        try:
            ok, msg = fn(c)
        except ValueError:
            raise
        except Exception:  # noqa: BLE001 - неожиданная структура файла не должна ронять сайт
            ok, msg = False, L(lang, "Не удалось проверить один из пунктов", "Бір тармақты тексеру мүмкін болмады")
        if c.get("msg"):
            msg = c["msg"][1] if lang == "kk" and isinstance(c["msg"], list) else (c["msg"][0] if isinstance(c["msg"], list) else c["msg"])
        results.append({"ok": bool(ok), "msg": msg})
    return results, None
