"""Кабинет учителя (классы по коду) и сертификаты о прохождении курса."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.ui import get_lang

from . import services
from .models import Certificate, Classroom, Course, Membership, Submission, Task
from .ui import course_texts


def _ctx(request, **extra):
    lang = get_lang(request)
    return {"ct": course_texts(lang), "points": services.user_points(request.user), **extra}


def _teacher_required(view):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not services.is_teacher(request.user):
            messages.info(request, course_texts(get_lang(request))["teacher_only"])
            return redirect("home")
        return view(request, *args, **kwargs)
    wrapper.__name__ = view.__name__
    return wrapper


def _my_class(request, pk):
    qs = Classroom.objects.all() if request.user.is_superuser else Classroom.objects.filter(teacher=request.user)
    return get_object_or_404(qs, pk=pk)


# ------------------------------------------------------------------ учитель

@_teacher_required
def teacher_home(request):
    ct = course_texts(get_lang(request))
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()[:100]
        if name:
            room = Classroom.objects.create(teacher=request.user, name=name)
            messages.success(request, f"{ct['class_created']} {room.code}")
            return redirect("teacher_class", room.pk)
    rooms = Classroom.objects.filter(teacher=request.user).annotate(n=Count("memberships"))
    return render(request, "course/teacher_home.html", _ctx(request, rooms=rooms))


@_teacher_required
def teacher_class(request, pk):
    lang = get_lang(request)
    room = _my_class(request, pk)
    courses = list(Course.objects.all())
    if not courses:
        raise Http404
    current = next((c for c in courses if c.slug == request.GET.get("course")), courses[0])
    students = [m.student for m in room.memberships.select_related("student").order_by(
        "student__last_name", "student__first_name", "student__username")]
    lessons, rows = services.group_progress(current, students)
    join_url = request.build_absolute_uri(reverse("join_class_code", args=[room.code]))
    return render(request, "course/teacher_class.html", _ctx(
        request, room=room, lessons=lessons, rows=rows, current=current, join_url=join_url,
        courses=[{"course": c, "title": c.title(lang)} for c in courses]))


@_teacher_required
def teacher_student(request, pk, user_id):
    lang = get_lang(request)
    room = _my_class(request, pk)
    m = get_object_or_404(Membership.objects.select_related("student"), classroom=room, student_id=user_id)
    student = m.student
    summary = []
    for c in Course.objects.all():
        solved, total = services.course_progress(student, c)
        if solved:
            summary.append({"course": c, "title": c.title(lang), "solved": solved, "total": total,
                            "percent": round(100 * solved / total) if total else 0,
                            "cert": Certificate.objects.filter(user=student, course=c).first()})
    from .models import ModuleTestResult
    tests = [{"course": r.module.course.title(lang), "module": r.module.number, "best": r.best, "total": r.total,
              "passed": r.passed, "attempts": r.attempts}
             for r in ModuleTestResult.objects.filter(user=student).select_related("module__course")
             .order_by("module__course__order", "module__number")]
    subs = (Submission.objects.filter(user=student).select_related("task__lesson__course")
            .order_by("-updated_at")[:40])
    recent = [{"sub": s, "task_title": s.task.title(lang), "course": s.task.lesson.course.title(lang),
               "lesson": s.task.lesson.number,
               "show_code": s.task.kind not in (Task.Kind.QUIZ,)} for s in subs]
    return render(request, "course/teacher_student.html", _ctx(
        request, room=room, student=student, summary=summary, recent=recent, tests=tests))


@_teacher_required
@require_POST
def teacher_remove_student(request, pk, user_id):
    room = _my_class(request, pk)
    Membership.objects.filter(classroom=room, student_id=user_id).delete()
    messages.info(request, course_texts(get_lang(request))["student_removed"])
    return redirect("teacher_class", room.pk)


@_teacher_required
@require_POST
def teacher_delete_class(request, pk):
    room = _my_class(request, pk)
    room.delete()
    messages.info(request, course_texts(get_lang(request))["class_deleted"])
    return redirect("teacher_home")


# ------------------------------------------------------------------ ученик

@login_required
def join_class(request, code=""):
    ct = course_texts(get_lang(request))
    code = (request.POST.get("code") or code or "").strip().upper()
    error = ""
    if request.method == "POST":
        room = Classroom.objects.filter(code=code).select_related("teacher").first()
        if room is None:
            error = ct["class_not_found"]
        else:
            _, created = Membership.objects.get_or_create(classroom=room, student=request.user)
            teacher = room.teacher.get_full_name() or room.teacher.username
            messages.success(request, f"{ct['joined'] if created else ct['already_joined']} «{room.name}» ({teacher})")
            return redirect("home")
    mine = Membership.objects.filter(student=request.user).select_related("classroom__teacher")
    return render(request, "course/join.html", _ctx(request, code=code, error=error, mine=mine))


# ------------------------------------------------------------------ сертификаты

@login_required
def certificate(request, course):
    lang = get_lang(request)
    ct = course_texts(lang)
    course = get_object_or_404(Course, slug=course)
    cert = Certificate.objects.filter(user=request.user, course=course).first()
    if cert is None:
        if not services.course_complete(request.user, course):
            messages.info(request, ct["cert_not_yet"])
            return redirect("course_home", course.slug)
        if request.method == "POST":
            first = (request.POST.get("first_name") or "").strip()[:150]
            last = (request.POST.get("last_name") or "").strip()[:150]
            if first and last:
                request.user.first_name, request.user.last_name = first, last
                request.user.save(update_fields=["first_name", "last_name"])
                cert = services.issue_certificate(request.user, course)
                return redirect("certificate", course.slug)
        return render(request, "course/certificate_name.html", _ctx(request, course=course,
                                                                    course_title=course.title(lang)))
    return _render_certificate(request, cert, own=True)


def certificate_verify(request, code):
    cert = get_object_or_404(Certificate.objects.select_related("course"), code=code.upper())
    return _render_certificate(request, cert, own=request.user.is_authenticated and request.user == cert.user)


def _render_certificate(request, cert, own):
    lang = get_lang(request)
    course = cert.course
    lessons = course.lessons.count()
    tasks = Task.objects.filter(lesson__course=course).count()
    verify_url = request.build_absolute_uri(reverse("certificate_verify", args=[cert.code]))
    from .views import lessons_word
    stats = (f"{lessons} сабақ · {tasks} тапсырма шешілді" if lang == "kk"
             else f"{lessons} {lessons_word(lessons, lang)} · {tasks} {_tasks_word(tasks)} решено")
    return render(request, "course/certificate.html", _ctx(
        request, cert=cert, course_title=course.title(lang), lessons=lessons, tasks=tasks,
        verify_url=verify_url, own=own, stats=stats))


def _tasks_word(n):
    if n % 10 == 1 and n % 100 != 11:
        return "задание"
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return "задания"
    return "заданий"
