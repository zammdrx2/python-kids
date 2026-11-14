"""Рейтинг класса за неделю: место, герой, баллы, серия дней."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.ui import get_lang

from . import hero_art, services
from .models import Classroom, Membership
from .ui import course_texts


@login_required
def rating(request):
    lang = get_lang(request)
    ct = course_texts(lang)
    user = request.user
    mine = [m.classroom for m in Membership.objects.filter(student=user).select_related("classroom__teacher")]
    if services.is_teacher(user):
        own = Classroom.objects.filter(teacher=user) if not user.is_superuser else Classroom.objects.all()
        mine += [c for c in own.select_related("teacher") if c not in mine]
    room = None
    if request.GET.get("class", "").isdigit():
        room = next((c for c in mine if c.pk == int(request.GET["class"])), None)
    room = room or (mine[0] if mine else None)
    rows = []
    if room:
        for r in services.class_rating(room):
            look = r["hero"].look() if r["hero"] else {"gender": "m"}
            r["art"] = hero_art.render(look, crop="bust")
            r["name"] = r["user"].get_full_name() or r["user"].username
            r["me"] = r["user"].pk == user.pk
            rows.append(r)
    return render(request, "course/rating.html", {
        "ct": ct, "points": services.user_points(user), "room": room, "rooms": mine, "rows": rows,
        "week_start": services.week_start(), "streak": services.streak(user),
        "bonuses": [{"days": d, "points": p} for d, p in services.STREAK_BONUS.items()],
    })
