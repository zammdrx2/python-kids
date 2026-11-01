from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import SignUpForm
from .ui import SUPPORTED, get_lang


@require_POST
def set_language(request):
    lang = request.POST.get("lang")
    if lang in SUPPORTED:
        request.session["lang"] = lang
    next_url = request.POST.get("next", "/")
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = "/"
    return redirect(next_url)


def signup(request):
    lang = get_lang(request)
    form = SignUpForm(request.POST or None, lang=lang, initial={"class_code": request.GET.get("code", "")})
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        from course import services
        from course.models import Classroom, Membership
        if form.cleaned_data.get("role") == "teacher":
            services.make_teacher(user)
            return redirect("teacher_home")
        code = form.cleaned_data.get("class_code")
        if code:
            Membership.objects.get_or_create(classroom=Classroom.objects.get(code=code), student=user)
        return redirect("home")
    return render(request, "registration/signup.html", {"form": form})


def robots_txt(request):
    """Правила для поисковых роботов: служебные страницы не индексируем."""
    from django.http import HttpResponse
    from django.urls import reverse
    lines = ["User-agent: *", "Disallow: /admin/", "Disallow: /teacher/", "Disallow: /progress/",
             "Disallow: /join/", "Disallow: /task/", "Disallow: /certificate/",
             f"Sitemap: {request.build_absolute_uri(reverse('sitemap'))}"]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


def sitemap_xml(request):
    """Карта сайта: главная, страницы курсов и уроков."""
    from django.http import HttpResponse
    from django.urls import reverse
    from course.models import Course, Lesson
    urls = [reverse("home")]
    for c in Course.objects.all():
        urls.append(reverse("course_home", args=[c.slug]))
    for l in Lesson.objects.select_related("course").order_by("course__order", "number"):
        urls.append(reverse("course_lesson", args=[l.course.slug, l.number]))
    body = "".join(f"<url><loc>{request.build_absolute_uri(u)}</loc></url>" for u in urls)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>')
    return HttpResponse(xml, content_type="application/xml")
