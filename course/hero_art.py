"""
Герой ученика на рисунках художника Sutemo (бесплатные наборы для визуальных новелл,
коммерческое использование разрешено автором; см. static/hero/CREDITS.txt).

Персонаж собирается из прозрачных слоёв WebP одного размера: static/hero/<пол>/<слот>__<имя>[__<цвет>].webp
Порядок слоёв как в исходном PSD. Фон - из course/avatar.py (SVG).
"""
from __future__ import annotations

from django.templatetags.static import static
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

SIZE = {"f": (520, 857), "m": (520, 567)}  # размер слоёв в static/hero

COLORS = {
    "f": {"black": "#2B2B3A", "brown": "#7A4B2E", "blond": "#F2C75C", "silver": "#D7D9E3", "pink": "#F48FB1"},
    "m": {"black": "#2B2B3A", "brown": "#7A4B2E", "blond": "#F2C75C", "silver": "#D7D9E3", "red": "#C2453A"},
}

FACES = {
    "f": [("normal", "Спокойный", "Сабырлы"), ("smile_1", "Улыбка", "Күлкі"), ("smile_2", "Улыбка 2", "Күлкі 2"),
          ("smile_3", "Улыбка 3", "Күлкі 3"), ("happy_1", "Радость", "Қуаныш"), ("happy_2", "Радость 2", "Қуаныш 2"),
          ("smug", "Хитрый", "Айлакер"), ("awkward", "Смущение", "Ыңғайсыз"), ("surprised", "Удивление", "Таңдану"),
          ("sad", "Грусть", "Мұң"), ("annoyed", "Недоволен", "Наразы"), ("angry", "Злой", "Ашулы")],
    "m": [("normal", "Спокойный", "Сабырлы"), ("smile_1", "Улыбка", "Күлкі"), ("smile_2", "Улыбка 2", "Күлкі 2"),
          ("smile_3", "Улыбка 3", "Күлкі 3"), ("laugh", "Смех", "Күлу"), ("smirk", "Хитрый", "Айлакер"),
          ("surprised", "Удивление", "Таңдану"), ("sweat", "Неловко", "Ыңғайсыз"), ("sad", "Грусть", "Мұң"),
          ("angry_1", "Злой", "Ашулы")],
}

# id: (пол, слот, имя слоя, цена, ru, kk). Цена 0 - выдаётся сразу.
ITEMS = {
    # --- девушка: одежда
    "f_tee": ("f", "outfit", "t_shirt_1", 0, "Белая футболка", "Ақ футболка"),
    "f_tee2": ("f", "outfit", "t_shirt_2", 40, "Чёрная футболка", "Қара футболка"),
    "f_sailor": ("f", "outfit", "seifuku_1", 60, "Школьная форма", "Мектеп формасы"),
    "f_sailor2": ("f", "outfit", "seifuku_2", 80, "Школьная форма (тёмная)", "Мектеп формасы (қою)"),
    "f_pe": ("f", "outfit", "pe_uniform_1", 90, "Спортивный костюм", "Спорт киімі"),
    "f_pe2": ("f", "outfit", "pe_uniform_2", 90, "Спортивный костюм (бирюза)", "Спорт киімі (көгілдір)"),
    "f_pajamas": ("f", "outfit", "pajamas_1", 70, "Пижама с котиками", "Мысықты пижама"),
    "f_pajamas2": ("f", "outfit", "pajamas_2", 70, "Розовая пижама", "Қызғылт пижама"),
    "f_winter": ("f", "outfit", "winter_1", 110, "Зимний кардиган", "Қысқы кардиган"),
    "f_winter2": ("f", "outfit", "winter_2", 110, "Серый кардиган", "Сұр кардиган"),
    "f_dress": ("f", "outfit", "summer_dress", 130, "Летнее платье", "Жазғы көйлек"),
    "f_jacket": ("f", "outfit", "jacket", 160, "Модная куртка", "Сәнді күрте"),
    # --- девушка: волосы
    "f_back1": ("f", "hairback", "style_1", 0, "Короткие", "Қысқа"),
    "f_back2": ("f", "hairback", "style_2", 80, "Длинные", "Ұзын"),
    "f_back3": ("f", "hairback", "style_3", 100, "Кудряшки", "Бұйра"),
    "f_back4": ("f", "hairback", "style_4", 120, "Высокий хвост", "Биік құйрық"),
    "f_front1": ("f", "hairfront", "style_1", 0, "Чёлка", "Кекіл"),
    "f_front2": ("f", "hairfront", "style_2", 40, "Чёлка набок", "Қисық кекіл"),
    "f_front3": ("f", "hairfront", "style_3", 50, "Ровная чёлка", "Түзу кекіл"),
    "f_front4": ("f", "hairfront", "style_4", 60, "Открытый лоб", "Ашық маңдай"),
    "f_front5": ("f", "hairfront", "style_5", 70, "Пряди", "Шаш талшықтары"),
    "f_noacc": ("f", "acc", "", 0, "Без аксессуаров", "Аксессуарсыз"),
    "f_glasses": ("f", "acc", "glasses", 50, "Очки", "Көзілдірік"),
    # --- парень: одежда
    "m_raglan": ("m", "outfit", "casual_2_1", 0, "Футболка", "Футболка"),
    "m_tee": ("m", "outfit", "casual_2_2", 40, "Синяя футболка", "Көк футболка"),
    "m_shirt": ("m", "outfit", "school_uniform_2", 60, "Рубашка с галстуком", "Галстукты жейде"),
    "m_shirt2": ("m", "outfit", "office_4", 60, "Рубашка с серым галстуком", "Сұр галстукты жейде"),
    "m_school": ("m", "outfit", "school_uniform_1", 90, "Школьный пиджак", "Мектеп пиджагы"),
    "m_gakuran": ("m", "outfit", "school_uniform_3", 110, "Гакуран", "Гакуран"),
    "m_pe": ("m", "outfit", "p_e_uniform", 90, "Спортивный костюм", "Спорт киімі"),
    "m_hoodie": ("m", "outfit", "casual_3_1", 100, "Красное худи", "Қызыл худи"),
    "m_hoodie2": ("m", "outfit", "casual_3_3", 100, "Голубое худи", "Көгілдір худи"),
    "m_vest": ("m", "outfit", "vest", 110, "Жилет", "Жилет"),
    "m_winter": ("m", "outfit", "winter", 120, "Зимний шарф", "Қысқы шарф"),
    "m_blazer": ("m", "outfit", "casual_1_1", 130, "Серый пиджак", "Сұр пиджак"),
    "m_blazer2": ("m", "outfit", "casual_1_2", 130, "Чёрный пиджак", "Қара пиджак"),
    "m_suit": ("m", "outfit", "office_1", 150, "Костюм с галстуком", "Галстукты костюм"),
    "m_suit2": ("m", "outfit", "office_2", 150, "Чёрный костюм", "Қара костюм"),
    "m_shirt3": ("m", "outfit", "office_3", 70, "Белая рубашка", "Ақ жейде"),
    # --- парень: волосы
    "m_back1": ("m", "hairback", "short_1", 0, "Короткие", "Қысқа"),
    "m_back2": ("m", "hairback", "short_2", 40, "Короткие 2", "Қысқа 2"),
    "m_back3": ("m", "hairback", "short_3", 50, "Короткие 3", "Қысқа 3"),
    "m_back4": ("m", "hairback", "long_hair", 120, "Длинные", "Ұзын"),
    "m_front1": ("m", "hairfront", "short_1", 0, "Чёлка", "Кекіл"),
    "m_front2": ("m", "hairfront", "short_2", 40, "Растрёпанная", "Ұйпаланған"),
    "m_front3": ("m", "hairfront", "style_3", 60, "Длинная чёлка", "Ұзын кекіл"),
    "m_front4": ("m", "hairfront", "style_3_short", 60, "Средняя чёлка", "Орташа кекіл"),
    "m_front5": ("m", "hairfront", "style_4", 80, "Пробор", "Айыру"),
    "m_front6": ("m", "hairfront", "style_4_short", 80, "Пробор короткий", "Қысқа айыру"),
    "m_front7": ("m", "hairfront", "curly", 100, "Кудрявые", "Бұйра"),
    "m_noacc": ("m", "acc", "", 0, "Без аксессуаров", "Аксессуарсыз"),
    "m_glasses": ("m", "acc", "black_glasses", 50, "Очки", "Көзілдірік"),
    "m_glasses2": ("m", "acc", "circle_glasses", 60, "Круглые очки", "Дөңгелек көзілдірік"),
    "m_phones": ("m", "acc", "headphones", 80, "Наушники на шее", "Мойындағы құлаққап"),
    "m_phones2": ("m", "acc", "headphones_up", 90, "Наушники", "Құлаққап"),
}

DEFAULTS = {"f": {"outfit": "f_tee", "hairback": "f_back1", "hairfront": "f_front1", "acc": "f_noacc"},
            "m": {"outfit": "m_raglan", "hairback": "m_back1", "hairfront": "m_front1", "acc": "m_noacc"}}

SLOTS = ["outfit", "hairfront", "hairback", "acc", "bg"]


def free_items():
    return {k for k, v in ITEMS.items() if v[3] == 0}


def item_name(item_id, lang):
    from . import avatar
    if item_id in ITEMS:
        it = ITEMS[item_id]
        return it[5] if lang == "kk" else it[4]
    return avatar.item_name(item_id, lang)


def item_price(item_id):
    from . import avatar
    if item_id in ITEMS:
        return ITEMS[item_id][3]
    return avatar.ITEMS[item_id][1]


def item_slot(item_id):
    from . import avatar
    if item_id in ITEMS:
        return ITEMS[item_id][1]
    return avatar.ITEMS[item_id][0]


def _src(g, slot, name, color=None):
    return static(f"hero/{g}/{slot}__{name}" + (f"__{color}" if color else "") + ".webp")


def layers(look):
    """Пути слоёв снизу вверх."""
    g = look.get("gender", "m")
    c = look.get("hair_color", "brown")
    if c not in COLORS[g]:
        c = "brown"

    def name(slot):
        item = look.get(slot) or DEFAULTS[g][slot]
        if item not in ITEMS or ITEMS[item][0] != g:
            item = DEFAULTS[g][slot]
        return ITEMS[item][2]

    face = look.get("face") if look.get("face") in [f[0] for f in FACES[g]] else "smile_1"
    acc = name("acc")
    out = [_src(g, "hairback", name("hairback"), c), _src(g, "base", "body")]
    if g == "f":
        out += [_src(g, "blush", "blush1"), _src(g, "outfit", name("outfit")), _src(g, "hairfront", name("hairfront"), c),
                _src(g, "face", face)]
        if acc:
            out.append(_src(g, "acc", acc))
    else:
        if acc == "headphones":
            out.append(_src(g, "acc", "headphones"))
        out += [_src(g, "outfit", name("outfit")), _src(g, "face", face), _src(g, "hairfront", name("hairfront"), c)]
        if acc in ("black_glasses", "circle_glasses", "headphones_up"):
            out.append(_src(g, "acc", acc))
    return out


def render(look, crop=""):
    """HTML героя: фон SVG и слои-картинки друг на друге. crop="bust" - крупный план головы."""
    from . import avatar
    g = look.get("gender", "m")
    w, h = SIZE[g]
    bg = avatar._bg(look.get("bg", "bg_room"))
    imgs = format_html_join("", '<img src="{}" alt="" loading="lazy" decoding="async">', ((s,) for s in layers(look)))
    return format_html('<div class="hero-art hero-art--{} {}" style="--ar: {} / {}">'
                       '<svg class="hero-art__bg" viewBox="0 0 240 300" preserveAspectRatio="xMidYMid slice" aria-hidden="true">{}</svg>'
                       '{}</div>', g, "hero-art--bust" if crop == "bust" else "", w, h, mark_safe(bg), imgs)
