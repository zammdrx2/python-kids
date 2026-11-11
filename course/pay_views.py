"""Платный доступ: страница оплаты для ученика и страница отметки оплат для администратора.

Оплата идёт через Kaspi (QR самозанятого). Сайт не видит платежи сам, поэтому
администратор после поступления денег нажимает «+1 месяц» у ученика.
"""
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.ui import get_lang

from . import services
from .models import Payment, Subscription
from .ui import course_texts


def pay(request):
    lang = get_lang(request)
    ct = course_texts(lang)
    until = services.paid_until(request.user)
    today = timezone.localdate()
    active = bool(until and until >= today)
    wa_text = ""
    if request.user.is_authenticated:
        name = request.user.get_full_name() or request.user.username
        wa_text = ct["pay_wa_text"].format(name=name, login=request.user.username, price=settings.PRICE_MONTH)
    return render(request, "course/pay.html", {
        "ct": ct, "points": services.user_points(request.user),
        "price": settings.PRICE_MONTH, "free": settings.FREE_LESSONS, "kaspi_url": settings.KASPI_PAY_URL,
        "wa_url": f"https://wa.me/{settings.PAY_WHATSAPP}?text={quote(wa_text)}",
        "price_fmt": f"{settings.PRICE_MONTH:,}".replace(",", " "),
        "pay_lead": ct["pay_lead"].format(free=settings.FREE_LESSONS),
        "pay_step2": ct["pay_step2"].format(price=f"{settings.PRICE_MONTH:,}".replace(",", " ")),
        "until": until, "active": active, "days_left": (until - today).days if active else 0,
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
    users = users.order_by("-last_login", "-date_joined")[:100]
    rows = []
    for u in users:
        until = getattr(getattr(u, "subscription", None), "paid_until", None)
        state = "none" if not until else ("active" if until >= today else "expired")
        rows.append({"user": u, "until": until, "state": state,
                     "soon": state == "active" and (until - today).days <= 3})
    stats = {
        "active": Subscription.objects.filter(paid_until__gte=today).count(),
        "month_sum": sum(Payment.objects.filter(created_at__year=today.year, created_at__month=today.month)
                         .values_list("amount", flat=True)),
    }
    return render(request, "course/payments.html", {
        "ct": course_texts(lang), "rows": rows, "q": q, "show": show, "price": settings.PRICE_MONTH,
        "recent": Payment.objects.select_related("user")[:15], "stats": stats, "today": today,
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
