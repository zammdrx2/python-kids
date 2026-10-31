"""
Логика курса: приём результатов проверки, прогресс ученика и группы.

Код выполняется в браузере ученика (Pyodide), поэтому сервер получает только
итог проверки. Для детского курса этого достаточно: преподаватель видит код
каждого решения и может проверить его в админке.
"""
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone

from .models import Lesson, Submission, Task


@transaction.atomic
def record_submission(user, task: Task, code: str, passed: int, total: int) -> Submission:
    code = (code or "")[:20000]
    sub, _ = Submission.objects.select_for_update().get_or_create(user=user, task=task)
    sub.code = code
    sub.attempts += 1

    if task.kind == Task.Kind.PROJECT:
        ok = bool(code.strip()) and code.strip() != task.starter_code.strip()
        sub.passed_tests, sub.total_tests = int(ok), 1
    else:
        expected = len(task.tests)
        total = expected  # число тестов берём с сервера, а не от клиента
        passed = max(0, min(int(passed), expected))
        ok = expected > 0 and passed == expected
        # лучший результат не ухудшается от неудачной попытки
        if ok or passed >= sub.passed_tests or not sub.solved:
            sub.passed_tests, sub.total_tests = passed, total

    if ok and not sub.solved:
        sub.solved = True
        sub.solved_at = timezone.now()
    sub.save()
    return sub


def lesson_progress(user) -> dict[int, dict]:
    """{id урока: {"solved": n, "total": m}} для одного ученика."""
    totals = dict(Lesson.objects.annotate(n=Count("tasks")).values_list("id", "n"))
    solved = {}
    if user.is_authenticated:
        solved = dict(
            Submission.objects.filter(user=user, solved=True)
            .values("task__lesson").annotate(n=Count("id")).values_list("task__lesson", "n")
        )
    return {lid: {"solved": solved.get(lid, 0), "total": n} for lid, n in totals.items()}


def lesson_access(user, progress=None) -> dict[int, bool]:
    """{id урока: открыт ли}. Урок открывается, когда решены все задания предыдущего.
    Преподавателю (is_staff) открыто всё; гостю — только первый урок."""
    if progress is None:
        progress = lesson_progress(user)
    access, prev_done, course_id = {}, True, None
    for lesson in Lesson.objects.order_by("course_id", "number"):
        if lesson.course_id != course_id:  # в каждом курсе первый урок открыт
            course_id, prev_done = lesson.course_id, True
        access[lesson.id] = bool(getattr(user, "is_staff", False)) or prev_done
        p = progress.get(lesson.id, {"solved": 0, "total": 0})
        prev_done = user.is_authenticated and p["total"] > 0 and p["solved"] >= p["total"]
    return access


def is_lesson_open(user, lesson) -> bool:
    return lesson_access(user).get(lesson.id, False)


def user_points(user) -> int:
    if not user.is_authenticated:
        return 0
    return Submission.objects.filter(user=user, solved=True).aggregate(s=Sum("task__points"))["s"] or 0


def group_progress(course):
    """Таблица для преподавателя: ученики × уроки одного курса."""
    lessons = list(Lesson.objects.filter(course=course).annotate(n=Count("tasks")).order_by("number"))
    User = get_user_model()
    in_course = Submission.objects.filter(task__lesson__course=course)
    students = (User.objects.filter(is_staff=False, id__in=in_course.values("user"))
                .order_by("last_name", "first_name", "username"))
    points = dict(in_course.filter(solved=True).values("user").annotate(p=Sum("task__points")).values_list("user", "p"))
    solved = {}
    for row in (Submission.objects.filter(solved=True, user__in=students)
                .values("user", "task__lesson").annotate(n=Count("id"))):
        solved[(row["user"], row["task__lesson"])] = row["n"]

    rows = []
    for s in students:
        cells = []
        done = 0
        for lesson in lessons:
            n = solved.get((s.id, lesson.id), 0)
            state = "done" if lesson.n and n == lesson.n else ("part" if n else "none")
            done += state == "done"
            cells.append({"n": n, "total": lesson.n, "state": state})
        rows.append({"user": s, "cells": cells, "points": points.get(s.id, 0), "done": done})
    return lessons, rows
