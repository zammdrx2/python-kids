import json

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from core.ui import get_lang

from . import services
from .models import Lesson, Module, Submission, Task
from .ui import course_texts


def course_home(request):
    lang = get_lang(request)
    progress = services.lesson_progress(request.user)
    modules = []
    for m in Module.objects.prefetch_related("lessons"):
        lessons = [{
            "lesson": l, "title": l.title(lang), "progress": progress.get(l.id, {"solved": 0, "total": 0}),
        } for l in m.lessons.all()]
        modules.append({"module": m, "title": m.title(lang), "lessons": lessons})
    done = sum(1 for p in progress.values() if p["total"] and p["solved"] == p["total"])
    return render(request, "course/home.html", {
        "modules": modules, "ct": course_texts(lang), "points": services.user_points(request.user),
        "done": done, "lesson_count": len(progress),
    })


def lesson_detail(request, number):
    lang = get_lang(request)
    lesson = get_object_or_404(Lesson.objects.select_related("module"), number=number)
    subs = {}
    if request.user.is_authenticated:
        subs = {s.task_id: s for s in Submission.objects.filter(user=request.user, task__lesson=lesson)}
    tasks = []
    for t in lesson.tasks.all():
        s = subs.get(t.id)
        tasks.append({
            "task": t, "title": t.title(lang), "text": t.text(lang), "hint": t.hint(lang),
            "code": s.code if s and s.code else t.starter_code,
            "solved": bool(s and s.solved),
            "example_input": t.tests[0]["input"] if t.tests else "",
            # JSON для страницы; "<" экранируем, чтобы код вроде "</script>" не ломал HTML
            "data_json": json.dumps({"tests": t.tests, "starter": t.starter_code}, ensure_ascii=False).replace("<", "\\u003c"),
        })
    prev_lesson = Lesson.objects.filter(number__lt=number).order_by("-number").first()
    next_lesson = Lesson.objects.filter(number__gt=number).order_by("number").first()
    return render(request, "course/lesson.html", {
        "lesson": lesson, "title": lesson.title(lang), "goal": lesson.goal(lang),
        "module_title": lesson.module.title(lang), "theory": lesson.theory_blocks(lang),
        "tasks": tasks, "prev": prev_lesson, "next": next_lesson, "ct": course_texts(lang),
        "pyodide_url": settings.PYODIDE_URL,
    })


@login_required
@require_POST
def submit(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    try:
        data = json.loads(request.body or "{}")
        passed = int(data.get("passed", 0))
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "bad request"}, status=400)
    sub = services.record_submission(request.user, task, str(data.get("code", "")), passed, len(task.tests))
    return JsonResponse({"ok": True, "solved": sub.solved, "passed": sub.passed_tests, "total": sub.total_tests})


@staff_member_required
def group_progress(request):
    lang = get_lang(request)
    lessons, rows = services.group_progress()
    return render(request, "course/progress.html", {"lessons": lessons, "rows": rows, "ct": course_texts(lang)})
