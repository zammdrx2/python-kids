"""Платный доступ: страница оплаты для ученика и страница отметки оплат для администратора.

Оплата идёт через Kaspi (QR самозанятого). Сайт не видит платежи сам, поэтому
администратор после поступления денег нажимает «+1 месяц» у ученика.
"""
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.ui import get_lang

from . import services
from .models import Classroom, Membership, Payment, Subscription
from .ui import course_texts


def pay(request):
    lang = get_lang(request)
    ct = course_texts(lang)
    kind, info = services.access_info(request.user)
    until = info if kind in ("paid", None) else None
    today = timezone.localdate()
    active = kind == "paid"
    price = services.user_price(request.user)
    wa_text = ""
    if request.user.is_authenticated:
        name = request.user.get_full_name() or request.user.username
        wa_text = ct["pay_wa_text"].format(name=name, login=request.user.username, price=services.fmt_price(price))
    return render(request, "course/pay.html", {
        "ct": ct, "points": services.user_points(request.user),
        "price": price, "free": settings.FREE_LESSONS, "class_discount": price == settings.CLASS_PRICE != settings.PRICE_MONTH,
        "full_price_fmt": services.fmt_price(settings.PRICE_MONTH), "kaspi_url": settings.KASPI_PAY_URL,
        "wa_url": f"https://wa.me/{settings.PAY_WHATSAPP}?text={quote(wa_text)}",
        "price_fmt": services.fmt_price(price),
        "pay_lead": ct["pay_lead"].format(free=settings.FREE_LESSONS),
        "pay_step2": ct["pay_step2"].format(price=services.fmt_price(price)),
        "until": until, "active": active, "free_kind": kind if kind in ("free", "class") else "",
        "free_class": info if kind == "class" else "", "days_left": (until - today).days if active else 0,
    })


@staff_member_required
def payments(request):
    """Список учеников с датой окончания доступа и кнопкой «+1 месяц»."""
    lang = get_lang(request)
    User = get_user_model()
    q = (request.GET.get("q") or "").strip()
    show = request.GET.get("show", "")
    users = User.objects.filter(is_staff=False).select_related("subscription")
    if q:
        users = users.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
                             | Q(email__icontains=q))
    today = timezone.localdate()
    if show == "active":
        users = users.filter(subscription__paid_until__gte=today)
    elif show == "expired":
        users = users.filter(subscription__paid_until__lt=today)
    elif show == "myclass":
        users = users.filter(memberships__classroom__teacher__is_staff=True).distinct()
    elif show == "noclass":
        users = users.filter(memberships__isnull=True)
    elif show == "free":
        users = users.filter(Q(subscription__free=True) | Q(memberships__classroom__free_access=True)).distinct()
    users = users.order_by("-last_login", "-date_joined")[:100]
    in_free_class = set(Membership.objects.filter(classroom__free_access=True).values_list("student_id", flat=True))
    in_my_class = set(Membership.objects.filter(classroom__teacher__is_staff=True).values_list("student_id", flat=True))
    class_names = {}
    for sid, name in Membership.objects.filter(student__in=[u.id for u in users]).values_list("student_id", "classroom__name"):
        class_names.setdefault(sid, []).append(name)
    rows = []
    for u in users:
        s = getattr(u, "subscription", None)
        until = getattr(s, "paid_until", None)
        state = "none" if not until else ("active" if until >= today else "expired")
        free = bool(s and s.free)
        price = settings.CLASS_PRICE if u.id in in_my_class else settings.PRICE_MONTH
        rows.append({"user": u, "until": until, "state": state, "free": free, "free_class": u.id in in_free_class,
                     "price": price, "price_fmt": services.fmt_price(price), "my_class": u.id in in_my_class,
                     "classes": ", ".join(class_names.get(u.id, [])),
                     "soon": state == "active" and (until - today).days <= 3})
    stats = {
        "active": Subscription.objects.filter(paid_until__gte=today).count(),
        "month_sum": sum(Payment.objects.filter(created_at__year=today.year, created_at__month=today.month)
                         .values_list("amount", flat=True)),
    }
    return render(request, "course/payments.html", {
        "ct": course_texts(lang), "rows": rows, "q": q, "show": show,
        "recent": Payment.objects.select_related("user")[:15], "stats": stats, "today": today,
        "classes": Classroom.objects.select_related("teacher").annotate(n=Count("memberships")),
    })


@staff_member_required
@require_POST
def payment_add(request, user_id):
    user = get_object_or_404(get_user_model(), pk=user_id, is_staff=False)
    try:
        months = max(1, min(12, int(request.POST.get("months", 1))))
    except ValueError:
        months = 1
    sub = services.extend_subscription(user, months, by=request.user)
    ct = course_texts(get_lang(request))
    messages.success(request, ct["payment_added"].format(
        name=user.get_full_name() or user.username, date=sub.paid_until.strftime("%d.%m.%Y")))
    back = request.POST.get("next") or ""
    return redirect(back if back.startswith("/") and not back.startswith("//") else "payments")


def _back(request):
    back = request.POST.get("next") or ""
    return redirect(back if back.startswith("/") and not back.startswith("//") else "payments")


@staff_member_required
@require_POST
def payment_free(request, user_id):
    """Включить/выключить бесплатный доступ ученику."""
    user = get_object_or_404(get_user_model(), pk=user_id, is_staff=False)
    free = request.POST.get("free") == "1"
    services.set_free(user, free)
    ct = course_texts(get_lang(request))
    messages.success(request, (ct["free_on"] if free else ct["free_off"]).format(name=user.get_full_name() or user.username))
    return _back(request)


@staff_member_required
@require_POST
def class_free(request, pk):
    """Бесплатный доступ всем ученикам класса (и тем, кто вступит позже)."""
    room = get_object_or_404(Classroom, pk=pk)
    room.free_access = request.POST.get("free") == "1"
    room.save(update_fields=["free_access"])
    ct = course_texts(get_lang(request))
    messages.success(request, (ct["class_free_on"] if room.free_access else ct["class_free_off"]).format(name=room.name))
    return _back(request)
