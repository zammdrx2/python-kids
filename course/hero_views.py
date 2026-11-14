"""Мой герой: персонаж ученика и магазин вещей за баллы."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.safestring import mark_safe

from core.ui import get_lang

from . import avatar, services
from .ui import course_texts

SLOT_ORDER = ["hair", "top", "hat", "weapon", "bg"]


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
                if h.hair == avatar.default_hair(h.gender):  # стандартная причёска меняется вместе с полом
                    h.hair = avatar.default_hair(gender)
                h.gender = gender
            for field, allowed in (("skin", avatar.SKINS), ("eye", avatar.EYES), ("hair_color", avatar.HAIR_COLORS)):
                v = request.POST.get(field)
                if v in allowed:
                    setattr(h, field, v)
            h.save()
        elif action in ("buy", "wear"):
            item = request.POST.get("item", "")
            if item in avatar.ITEMS:
                if action == "wear" and item not in services.owned_items(request.user):
                    messages.info(request, ct["hero_not_owned"])
                else:
                    try:
                        services.buy_item(request.user, item)
                        if action == "buy" and avatar.ITEMS[item][1]:
                            messages.success(request, ct["hero_bought"].format(name=avatar.item_name(item, lang)))
                    except services.NotEnoughPoints:
                        messages.info(request, ct["hero_no_points"])
        slot = request.POST.get("slot") or request.GET.get("slot") or "hair"
        return redirect(f"{request.path}?slot={slot}")

    slot = request.GET.get("slot") if request.GET.get("slot") in SLOT_ORDER else "hair"
    owned = services.owned_items(request.user)
    balance = services.user_points(request.user)
    items = []
    for item_id, (s, price, ru, kk) in avatar.ITEMS.items():
        if s != slot:
            continue
        items.append({"id": item_id, "name": kk if lang == "kk" else ru, "price": price,
                      "owned": item_id in owned, "worn": getattr(h, slot) == item_id,
                      "can_buy": balance >= price, "need": max(0, price - balance),
                      "preview": mark_safe(avatar.render_tall(h.look(**{slot: item_id}),
                                                                  crop="bust" if slot in ("hair", "hat") else ""))})
    items.sort(key=lambda i: (i["price"], i["name"]))
    return render(request, "course/hero.html", {
        "ct": ct, "points": balance, "hero": h, "svg": mark_safe(avatar.render_tall(h.look())),
        "slot": slot, "slots": [{"id": s, "title": ct[f"slot_{s}"]} for s in SLOT_ORDER], "items": items,
        "earned": services.points_earned(request.user),
        "skins": [{"id": k, "color": v[0]} for k, v in avatar.SKINS.items()],
        "eyes": [{"id": k, "color": v} for k, v in avatar.EYES.items()],
        "hair_colors": [{"id": k, "color": v} for k, v in avatar.HAIR_COLORS.items()],
    })
