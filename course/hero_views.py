"""Мой герой: персонаж ученика и магазин вещей за баллы."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from core.ui import get_lang

from . import avatar, hero_art, services
from .ui import course_texts

SLOTS = hero_art.SLOTS


def _switch_gender(h, gender):
    """Новый пол: вещи другого пола заменяются стандартными, цвет волос - если такого нет."""
    h.gender = gender
    for slot, default in hero_art.DEFAULTS[gender].items():
        item = getattr(h, slot)
        if item not in hero_art.ITEMS or hero_art.ITEMS[item][0] != gender:
            setattr(h, slot, default)
    if h.hair_color not in hero_art.COLORS[gender]:
        h.hair_color = "brown"
    if h.face not in [f[0] for f in hero_art.FACES[gender]]:
        h.face = "smile_1"


@login_required
def hero(request):
    lang = get_lang(request)
    ct = course_texts(lang)
    h = services.get_hero(request.user)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "look":
            gender = request.POST.get("gender")
            if gender in ("m", "f") and gender != h.gender:
                _switch_gender(h, gender)
            else:
                if request.POST.get("hair_color") in hero_art.COLORS[h.gender]:
                    h.hair_color = request.POST["hair_color"]
                if request.POST.get("face") in [f[0] for f in hero_art.FACES[h.gender]]:
                    h.face = request.POST["face"]
            h.save()
        elif action in ("buy", "wear"):
            item = request.POST.get("item", "")
            if action == "wear" and item not in services.owned_items(request.user):
                messages.info(request, ct["hero_not_owned"])
            else:
                try:
                    services.buy_item(request.user, item)
                    if action == "buy" and hero_art.item_price(item):
                        messages.success(request, ct["hero_bought"].format(name=hero_art.item_name(item, lang)))
                except services.NotEnoughPoints:
                    messages.info(request, ct["hero_no_points"])
                except (ValueError, KeyError):
                    pass
        slot = request.POST.get("slot") or "outfit"
        return redirect(f"{request.path}?slot={slot if slot in SLOTS else 'outfit'}")

    slot = request.GET.get("slot") if request.GET.get("slot") in SLOTS else "outfit"
    owned = services.owned_items(request.user)
    balance = services.user_points(request.user)
    if slot == "bg":
        catalog = [(k, v[1], v[2], v[3]) for k, v in avatar.ITEMS.items() if v[0] == "bg"]
    else:
        catalog = [(k, v[3], v[4], v[5]) for k, v in hero_art.ITEMS.items() if v[0] == h.gender and v[1] == slot]
    items = []
    for item_id, price, ru, kk in catalog:
        items.append({"id": item_id, "name": kk if lang == "kk" else ru, "price": price,
                      "owned": item_id in owned, "worn": getattr(h, slot) == item_id,
                      "can_buy": balance >= price, "need": max(0, price - balance),
                      "preview": hero_art.render(h.look(**{slot: item_id}),
                                                 crop="bust" if slot in ("hairfront", "hairback", "acc") else "")})
    items.sort(key=lambda i: (i["price"], i["name"]))
    return render(request, "course/hero.html", {
        "ct": ct, "points": balance, "hero": h, "art": hero_art.render(h.look()),
        "slot": slot, "slots": [{"id": s, "title": ct[f"slot_{s}"]} for s in SLOTS], "items": items,
        "earned": services.points_earned(request.user),
        "hair_colors": [{"id": k, "color": v} for k, v in hero_art.COLORS[h.gender].items()],
        "faces": [{"id": f[0], "name": f[2] if lang == "kk" else f[1]} for f in hero_art.FACES[h.gender]],
    })
