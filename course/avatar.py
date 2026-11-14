"""
Герой ученика: персонаж в стиле аниме (чиби), которого можно одевать за баллы.

Персонаж собирается из слоёв SVG: фон, волосы сзади, ноги, одежда, руки, оружие,
голова, лицо, чёлка, головной убор. Все рисунки - собственные, нарисованы кодом.
Каталог ITEMS: у каждой вещи слот, цена в баллах и название на двух языках.
"""
from __future__ import annotations

from html import escape

SKINS = {"light": ("#FFE3D1", "#F4C4A8"), "tan": ("#F2C49B", "#DDA37A"), "brown": ("#C98B5E", "#A86E46")}
EYES = {"brown": "#7A4A2A", "blue": "#3A7BD5", "green": "#3FA36B", "violet": "#8A5CD6"}
HAIR_COLORS = {"black": "#2B2B3A", "brown": "#7A4B2E", "blond": "#F2C75C", "pink": "#F48FB1",
               "blue": "#5C8DF2", "white": "#EDEDF5", "red": "#D9483B"}

SLOTS = ["bg", "hair", "top", "hat", "weapon"]

# слот, цена, ru, kk. Цена 0 - выдаётся сразу.
ITEMS = {
    # фоны
    "bg_room": ("bg", 0, "Комната", "Бөлме"),
    "bg_sakura": ("bg", 80, "Сакура", "Сакура"),
    "bg_city": ("bg", 120, "Ночной город", "Түнгі қала"),
    "bg_castle": ("bg", 160, "Замок", "Қамал"),
    "bg_space": ("bg", 250, "Космос", "Ғарыш"),
    # причёски
    "hair_spiky": ("hair", 0, "Ёжик", "Кірпі"),
    "hair_long": ("hair", 0, "Длинные волосы", "Ұзын шаш"),
    "hair_bob": ("hair", 40, "Каре", "Каре"),
    "hair_pony": ("hair", 60, "Хвост", "Құйрық шаш"),
    "hair_twins": ("hair", 80, "Два хвостика", "Екі құйрық"),
    "hair_hero": ("hair", 100, "Причёска героя", "Батыр шашы"),
    # одежда
    "top_tee": ("top", 0, "Футболка", "Футболка"),
    "top_hoodie": ("top", 60, "Худи программиста", "Бағдарламашы худиі"),
    "top_school": ("top", 80, "Школьная форма", "Мектеп формасы"),
    "top_ninja": ("top", 150, "Костюм ниндзя", "Ниндзя киімі"),
    "top_wizard": ("top", 180, "Мантия мага", "Сиқыршы шапаны"),
    "top_knight": ("top", 220, "Доспехи рыцаря", "Сері сауыты"),
    "top_space": ("top", 300, "Скафандр", "Скафандр"),
    # головные уборы
    "hat_none": ("hat", 0, "Без шапки", "Бас киімсіз"),
    "hat_cap": ("hat", 50, "Кепка", "Кепка"),
    "hat_cat": ("hat", 70, "Кошачьи ушки", "Мысық құлақтары"),
    "hat_phones": ("hat", 90, "Наушники", "Құлаққап"),
    "hat_wizard": ("hat", 130, "Шляпа мага", "Сиқыршы қалпағы"),
    "hat_crown": ("hat", 350, "Корона", "Тәж"),
    # оружие
    "weapon_none": ("weapon", 0, "Без оружия", "Қарусыз"),
    "weapon_wood": ("weapon", 100, "Деревянный меч", "Ағаш семсер"),
    "weapon_staff": ("weapon", 160, "Магический посох", "Сиқырлы таяқ"),
    "weapon_bow": ("weapon", 180, "Лук", "Садақ"),
    "weapon_hammer": ("weapon", 220, "Молот", "Балға"),
    "weapon_katana": ("weapon", 280, "Катана", "Катана"),
    "weapon_laser": ("weapon", 450, "Лазерный меч", "Лазер семсер"),
}

DEFAULTS = {"bg": "bg_room", "top": "top_tee", "hat": "hat_none", "weapon": "weapon_none"}


def default_hair(gender):
    return "hair_long" if gender == "f" else "hair_spiky"


def free_items():
    return {k for k, v in ITEMS.items() if v[1] == 0}


def item_name(item_id, lang):
    it = ITEMS[item_id]
    return it[3] if lang == "kk" else it[2]


# ------------------------------------------------------------------ слои

def _bg(item):
    if item == "bg_sakura":
        petals = "".join(f'<ellipse cx="{x}" cy="{y}" rx="5" ry="3" fill="#F7A8C4" transform="rotate({r} {x} {y})"/>'
                         for x, y, r in [(30, 40, 20), (200, 60, -30), (60, 120, 45), (210, 150, 10), (25, 210, -20),
                                         (190, 230, 35), (110, 30, 0)])
        return ('<rect width="240" height="300" fill="#FFE8F0"/><circle cx="210" cy="20" r="70" fill="#FBD0DF"/>'
                '<circle cx="20" cy="10" r="55" fill="#FBD0DF"/>' + petals)
    if item == "bg_city":
        b = "".join(f'<rect x="{x}" y="{y}" width="{w}" height="{300 - y}" fill="#2E2A5A"/>'
                    for x, y, w in [(0, 170, 40), (38, 130, 34), (72, 190, 30), (150, 140, 36), (186, 110, 30), (214, 180, 26)])
        win = "".join(f'<rect x="{x}" y="{y}" width="5" height="7" fill="#FFD66B"/>'
                      for x, y in [(10, 185), (22, 200), (46, 145), (58, 170), (160, 160), (172, 185), (194, 125), (202, 150), (220, 195)])
        return ('<rect width="240" height="300" fill="#1B1840"/><circle cx="190" cy="50" r="22" fill="#FFF4C2"/>'
                '<circle cx="40" cy="40" r="1.6" fill="#fff"/><circle cx="120" cy="25" r="1.4" fill="#fff"/>'
                '<circle cx="80" cy="70" r="1.2" fill="#fff"/>' + b + win)
    if item == "bg_castle":
        return ('<rect width="240" height="300" fill="#CDEBFF"/><circle cx="40" cy="50" r="24" fill="#FFF1A8"/>'
                '<path d="M140 210 V120 h12 v-10 h8 v10 h8 v-10 h8 v10 h8 v-10 h8 v10 h12 V210 Z" fill="#B9B3D8"/>'
                '<rect x="168" y="160" width="18" height="50" rx="9" fill="#7D74A8"/>'
                '<path d="M140 120 L164 80 L188 120 Z" fill="#E86A6A" transform="translate(-24 0) scale(1)"/>'
                '<rect x="0" y="210" width="240" height="90" fill="#9ED98A"/>')
    if item == "bg_space":
        stars = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff"/>'
                        for x, y, r in [(20, 30, 1.5), (70, 60, 1), (200, 40, 1.8), (150, 90, 1.2), (30, 160, 1.4),
                                        (215, 190, 1.1), (100, 20, 1), (180, 250, 1.5), (40, 260, 1.2)])
        return ('<rect width="240" height="300" fill="#141433"/><circle cx="195" cy="75" r="30" fill="#F2A65A"/>'
                '<ellipse cx="195" cy="75" rx="48" ry="9" fill="none" stroke="#FFD9A8" stroke-width="4"/>'
                '<circle cx="45" cy="95" r="14" fill="#7FD1C9"/>' + stars)
    return ('<rect width="240" height="300" fill="#EAF2FF"/><rect x="0" y="230" width="240" height="70" fill="#D7E3F7"/>'
            '<rect x="24" y="40" width="64" height="48" rx="6" fill="#fff" stroke="#C6D4EC" stroke-width="3"/>'
            '<path d="M30 80 L50 60 L64 72 L74 64 L82 80 Z" fill="#9ED98A"/>')


def _hair_back(item, c):
    if item == "hair_long":
        return f'<path d="M62 100 C58 40 182 40 178 100 L186 215 C170 225 150 210 150 200 L90 200 C90 210 70 225 54 215 Z" fill="{c}"/>'
    if item == "hair_bob":
        return f'<path d="M60 100 C56 42 184 42 180 100 L182 158 C160 168 80 168 58 158 Z" fill="{c}"/>'
    if item == "hair_pony":
        return (f'<path d="M150 60 C200 50 214 110 196 170 C190 190 176 196 172 180 C186 140 180 96 150 80 Z" fill="{c}"/>'
                f'<circle cx="160" cy="62" r="7" fill="#E8546B"/>')
    if item == "hair_twins":
        return (f'<path d="M70 70 C24 80 20 150 38 196 C46 210 60 205 58 190 C46 150 52 110 76 92 Z" fill="{c}"/>'
                f'<path d="M170 70 C216 80 220 150 202 196 C194 210 180 205 182 190 C194 150 188 110 164 92 Z" fill="{c}"/>'
                '<circle cx="72" cy="78" r="7" fill="#5CC8F2"/><circle cx="168" cy="78" r="7" fill="#5CC8F2"/>')
    return ""


def _hair_front(item, c):
    cap = "M64 104 C58 48 96 36 120 38 C144 36 182 48 176 104"
    if item == "hair_long":
        bangs = "L168 86 L156 100 L148 78 L134 96 L122 74 L110 96 L98 78 L86 100 L74 86 Z"
        side = (f'<path d="M64 100 C60 130 62 160 70 180 L80 176 C74 150 74 120 78 100 Z" fill="{c}"/>'
                f'<path d="M176 100 C180 130 178 160 170 180 L160 176 C166 150 166 120 162 100 Z" fill="{c}"/>')
        return f'<path d="{cap} {bangs}" fill="{c}"/>' + side
    if item == "hair_bob":
        return f'<path d="{cap} L170 92 C150 80 136 70 120 84 C104 70 90 80 70 92 Z" fill="{c}"/>'
    if item == "hair_twins" or item == "hair_pony":
        return f'<path d="{cap} L168 90 L150 96 L140 80 L120 92 L100 80 L90 96 L72 90 Z" fill="{c}"/>'
    if item == "hair_hero":
        return (f'<path d="M62 106 L50 70 L72 76 L66 40 L92 58 L100 22 L118 50 L138 20 L146 56 L172 38 L168 74 L192 68 '
                f'L178 106 L168 88 L156 100 L148 76 L134 96 L122 72 L110 96 L98 76 L86 100 L74 86 Z" fill="{c}"/>')
    # ёжик
    return f'<path d="{cap} L170 82 L158 96 L150 74 L136 92 L124 70 L112 92 L100 72 L88 96 L78 80 L68 98 Z" fill="{c}"/>'


def _legs(gender, top):
    if top == "top_space":
        return ('<rect x="88" y="244" width="28" height="44" rx="8" fill="#EDEFF7"/><rect x="124" y="244" width="28" height="44" rx="8" fill="#EDEFF7"/>'
                '<rect x="84" y="282" width="36" height="14" rx="7" fill="#6C7894"/><rect x="120" y="282" width="36" height="14" rx="7" fill="#6C7894"/>')
    pants = {"top_ninja": "#2B2B3A", "top_knight": "#8A93A8", "top_wizard": "#4B3C8C", "top_hoodie": "#3C4A6B"}.get(top, "#3C5A99")
    shoes = '<ellipse cx="101" cy="292" rx="17" ry="7" fill="#3A2A2A"/><ellipse cx="139" cy="292" rx="17" ry="7" fill="#3A2A2A"/>'
    if gender == "f" and top in ("top_tee", "top_school", "top_hoodie"):
        skirt = "#2F3F7A" if top == "top_school" else "#E86A8A"
        return (f'<rect x="92" y="250" width="20" height="40" fill="#FFE3D1"/><rect x="128" y="250" width="20" height="40" fill="#FFE3D1"/>'
                f'<path d="M80 236 L160 236 L172 272 L68 272 Z" fill="{skirt}"/>' + shoes)
    return (f'<rect x="88" y="244" width="28" height="46" rx="6" fill="{pants}"/>'
            f'<rect x="124" y="244" width="28" height="46" rx="6" fill="{pants}"/>' + shoes)


TORSO = "M84 178 Q120 166 156 178 L166 252 L74 252 Z"


def _top(item, skin):
    arms = lambda col: (f'<path d="M86 182 L64 236" stroke="{col}" stroke-width="20" stroke-linecap="round"/>'
                        f'<path d="M154 182 L176 236" stroke="{col}" stroke-width="20" stroke-linecap="round"/>')
    hands = f'<circle cx="64" cy="240" r="10" fill="{skin}"/><circle cx="176" cy="240" r="10" fill="{skin}"/>'
    if item == "top_hoodie":
        return (arms("#3E3E52") + f'<path d="{TORSO}" fill="#3E3E52"/>'
                '<path d="M98 176 Q120 196 142 176" fill="none" stroke="#2B2B3A" stroke-width="6"/>'
                '<rect x="100" y="222" width="40" height="20" rx="6" fill="#34344A"/>'
                '<text x="120" y="214" font-family="monospace" font-size="16" font-weight="700" fill="#7CE38B" text-anchor="middle">&lt;/&gt;</text>' + hands)
    if item == "top_school":
        return (arms("#F4F6FB") + f'<path d="{TORSO}" fill="#F4F6FB"/>'
                '<path d="M86 178 L120 210 L154 178 L146 176 L120 196 L94 176 Z" fill="#2F3F7A"/>'
                '<path d="M114 206 L120 222 L126 206 L120 200 Z" fill="#E8546B"/>' + hands)
    if item == "top_ninja":
        return (arms("#2B2B3A") + f'<path d="{TORSO}" fill="#2B2B3A"/>'
                '<path d="M86 180 L152 236" stroke="#3E3E58" stroke-width="10"/>'
                '<rect x="74" y="228" width="92" height="10" fill="#C0392B"/>' + hands)
    if item == "top_wizard":
        return (arms("#5B47A8") + '<path d="M84 178 Q120 166 156 178 L176 266 L64 266 Z" fill="#5B47A8"/>'
                '<path d="M120 172 L120 266" stroke="#F2C75C" stroke-width="4"/>'
                '<circle cx="104" cy="206" r="4" fill="#F2C75C"/><circle cx="140" cy="226" r="3" fill="#F2C75C"/>'
                '<path d="M134 196 l3 6 6 1-5 4 1 6-5-3-5 3 1-6-5-4 6-1z" fill="#F2C75C"/>' + hands)
    if item == "top_knight":
        return (arms("#A9B2C6") + f'<path d="{TORSO}" fill="#C3CBDB"/>'
                '<path d="M92 186 Q120 178 148 186 L150 230 Q120 244 90 230 Z" fill="#E1E6F0"/>'
                '<path d="M120 190 L120 232 M104 210 L136 210" stroke="#D9483B" stroke-width="6"/>'
                '<circle cx="84" cy="184" r="12" fill="#A9B2C6"/><circle cx="156" cy="184" r="12" fill="#A9B2C6"/>' + hands)
    if item == "top_space":
        return (arms("#EDEFF7") + f'<path d="{TORSO}" fill="#EDEFF7"/>'
                '<rect x="102" y="196" width="36" height="26" rx="6" fill="#5C8DF2"/>'
                '<circle cx="112" cy="209" r="4" fill="#FFD66B"/><circle cx="128" cy="209" r="4" fill="#7CE38B"/>'
                '<rect x="74" y="236" width="92" height="8" fill="#F2A65A"/>'
                '<circle cx="64" cy="240" r="11" fill="#6C7894"/><circle cx="176" cy="240" r="11" fill="#6C7894"/>')
    # футболка
    return (arms("#F2A65A") + f'<path d="{TORSO}" fill="#F2A65A"/>'
            '<path d="M106 176 Q120 186 134 176" fill="none" stroke="#D98A40" stroke-width="4"/>'
            '<text x="120" y="222" font-family="sans-serif" font-size="20" font-weight="800" fill="#fff" text-anchor="middle">Py</text>' + hands)


def _weapon(item):
    g = '<g transform="rotate(22 176 240)">{}</g>'
    if item == "weapon_wood":
        return g.format('<rect x="172" y="150" width="9" height="86" rx="3" fill="#C99A62"/>'
                        '<rect x="160" y="228" width="32" height="8" rx="3" fill="#8A5A2B"/><rect x="172" y="236" width="9" height="20" fill="#6B4423"/>')
    if item == "weapon_katana":
        return g.format('<path d="M174 130 L180 130 L182 230 L172 230 Z" fill="#E6ECF5" stroke="#9AA6BA" stroke-width="1.5"/>'
                        '<ellipse cx="177" cy="232" rx="14" ry="4" fill="#C9A227"/><rect x="173" y="234" width="8" height="26" fill="#2B2B3A"/>')
    if item == "weapon_staff":
        return ('<rect x="172" y="128" width="8" height="150" rx="4" fill="#8A5A2B"/>'
                '<circle cx="176" cy="122" r="15" fill="#A88BFF"/><circle cx="171" cy="117" r="5" fill="#fff" opacity=".8"/>'
                '<circle cx="176" cy="122" r="22" fill="none" stroke="#A88BFF" stroke-width="2" opacity=".5"/>')
    if item == "weapon_bow":
        return ('<path d="M188 160 Q220 240 188 320" fill="none" stroke="#8A5A2B" stroke-width="7" stroke-linecap="round" transform="translate(-4 -40)"/>'
                '<path d="M184 120 L184 280" stroke="#EDEDF5" stroke-width="1.5"/>')
    if item == "weapon_hammer":
        return g.format('<rect x="172" y="160" width="9" height="100" rx="3" fill="#8A5A2B"/>'
                        '<rect x="152" y="140" width="50" height="30" rx="6" fill="#8A93A8"/><rect x="152" y="148" width="50" height="6" fill="#6C7894"/>')
    if item == "weapon_laser":
        return g.format('<rect x="171" y="118" width="12" height="114" rx="6" fill="#5CF2E0" opacity=".45"/>'
                        '<rect x="174" y="120" width="6" height="110" rx="3" fill="#E9FFFC"/>'
                        '<rect x="170" y="230" width="14" height="28" rx="3" fill="#4B5568"/><rect x="170" y="236" width="14" height="4" fill="#C9D2E3"/>')
    return ""


def _hat(item):
    if item == "hat_cap":
        return ('<path d="M66 82 C66 40 174 40 174 82 Z" fill="#D9483B"/>'
                '<path d="M120 80 L196 80 Q200 92 186 92 L120 92 Z" fill="#B53A2F"/><circle cx="120" cy="46" r="5" fill="#B53A2F"/>')
    if item == "hat_cat":
        return ('<path d="M70 70 L74 26 L106 52 Z" fill="#2B2B3A"/><path d="M78 62 L80 38 L98 52 Z" fill="#F7A8C4"/>'
                '<path d="M170 70 L166 26 L134 52 Z" fill="#2B2B3A"/><path d="M162 62 L160 38 L142 52 Z" fill="#F7A8C4"/>')
    if item == "hat_phones":
        return ('<path d="M62 104 C56 30 184 30 178 104" fill="none" stroke="#3E3E52" stroke-width="9"/>'
                '<rect x="52" y="92" width="20" height="34" rx="8" fill="#5C8DF2"/><rect x="168" y="92" width="20" height="34" rx="8" fill="#5C8DF2"/>')
    if item == "hat_wizard":
        return ('<path d="M120 0 L170 66 L70 66 Z" fill="#5B47A8"/><ellipse cx="120" cy="68" rx="64" ry="12" fill="#4B3C8C"/>'
                '<path d="M118 28 l3 6 6 1-5 4 1 6-5-3-5 3 1-6-5-4 6-1z" fill="#F2C75C"/>')
    if item == "hat_crown":
        return ('<path d="M78 70 L84 30 L102 52 L120 22 L138 52 L156 30 L162 70 Z" fill="#F2C75C" stroke="#C9A227" stroke-width="3"/>'
                '<circle cx="120" cy="56" r="6" fill="#E8546B"/><circle cx="96" cy="60" r="4" fill="#5C8DF2"/><circle cx="144" cy="60" r="4" fill="#5C8DF2"/>')
    return ""


def _face(gender, skin, eye):
    s, sh = SKINS.get(skin, SKINS["light"])
    e = EYES.get(eye, EYES["brown"])
    head = (f'<ellipse cx="66" cy="110" rx="8" ry="11" fill="{s}"/><ellipse cx="174" cy="110" rx="8" ry="11" fill="{s}"/>'
            f'<path d="M66 100 C66 52 174 52 174 100 C174 136 150 160 120 163 C90 160 66 136 66 100 Z" fill="{s}"/>')
    eyes = ""
    for cx in (98, 142):
        lash_w = 4.5 if gender == "f" else 3.5
        flick = (f'<path d="M{cx + 13} 104 l6 -5" stroke="#2B2B3A" stroke-width="3" stroke-linecap="round"/>' if gender == "f" and cx == 142
                 else (f'<path d="M{cx - 13} 104 l-6 -5" stroke="#2B2B3A" stroke-width="3" stroke-linecap="round"/>' if gender == "f" else ""))
        eyes += (f'<ellipse cx="{cx}" cy="114" rx="13" ry="15" fill="#fff"/>'
                 f'<ellipse cx="{cx}" cy="116" rx="10" ry="13" fill="{e}"/>'
                 f'<ellipse cx="{cx}" cy="118" rx="5" ry="7" fill="#1E1A2E"/>'
                 f'<circle cx="{cx - 4}" cy="110" r="3.6" fill="#fff"/><circle cx="{cx + 4}" cy="122" r="1.8" fill="#fff"/>'
                 f'<path d="M{cx - 14} 104 Q{cx} 94 {cx + 14} 104" fill="none" stroke="#2B2B3A" stroke-width="{lash_w}" stroke-linecap="round"/>'
                 + flick)
    brows = ('<path d="M88 87 Q97 81 106 86" fill="none" stroke="#2B2B3A" stroke-width="2.5" stroke-linecap="round"/>'
             '<path d="M134 86 Q143 81 152 87" fill="none" stroke="#2B2B3A" stroke-width="2.5" stroke-linecap="round"/>')
    mouth = ('<path d="M113 140 Q120 147 127 140" fill="#E8546B" stroke="#B83A4E" stroke-width="2" stroke-linecap="round"/>'
             '<ellipse cx="86" cy="132" rx="9" ry="5" fill="#F48FB1" opacity=".45"/>'
             '<ellipse cx="154" cy="132" rx="9" ry="5" fill="#F48FB1" opacity=".45"/>')
    neck = f'<rect x="110" y="150" width="20" height="26" fill="{sh}"/>'
    return neck, head + eyes + brows + mouth


def render(look: dict, size: int | None = None) -> str:
    """look: gender, skin, eye, hair_color, и по одному предмету на слот."""
    gender = look.get("gender", "m")
    skin = look.get("skin", "light")
    hc = HAIR_COLORS.get(look.get("hair_color", "black"), HAIR_COLORS["black"])
    hair = look.get("hair") or default_hair(gender)
    top = look.get("top", "top_tee")
    neck, face = _face(gender, skin, look.get("eye", "brown"))
    s = SKINS.get(skin, SKINS["light"])[0]
    parts = [_bg(look.get("bg", "bg_room")), _hair_back(hair, hc), _legs(gender, top).replace("#FFE3D1", s), neck,
             _top(top, s), face, _hair_front(hair, hc), _hat(look.get("hat", "hat_none")), _weapon(look.get("weapon", "weapon_none"))]
    wh = f' width="{size}" height="{int(size * 1.25)}"' if size else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 300"{wh} role="img" aria-label="{escape("hero")}">'
            + "".join(parts) + "</svg>")
