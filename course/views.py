import json

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.views import redirect_to_login
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.ui import get_lang

from . import office_checks, services
from .models import Certificate, Course, Lesson, Module, ModuleTestResult, Submission, Task
from .ui import course_texts

MODULE_COLORS = ["#D3F26B", "#7FE3D5", "#A7BAFF", "#E6F7A8", "#B8EEE6", "#CCD7FF"]  # оттенки слоёв логотипа stack.

# Короткое описание модулей: (курс, номер модуля) -> (рус, қаз)
MODULE_DESC = {
    ("python", 1): ("print, переменные, input", "print, айнымалылар, input"),
    ("python", 2): ("if, elif, and / or", "if, elif, and / or"),
    ("python", 3): ("for, while, игра «Угадай число»", "for, while, «Санды тап» ойыны"),
    ("python", 4): ("срезы, методы, шифр Цезаря", "кесінділер, әдістер, Цезарь шифры"),
    ("python", 5): ("append, sort, журнал оценок", "append, sort, бағалар журналы"),
    ("python", 6): ("def, return, словари, своя игра", "def, return, сөздіктер, өз ойының"),
    ("web", 1): ("теги, заголовки, абзацы, списки", "тегтер, тақырыптар, абзацтар, тізімдер"),
    ("web", 2): ("ссылки, картинки, таблицы", "сілтемелер, суреттер, кестелер"),
    ("web", 3): ("цвета, шрифты, классы, блоки", "түстер, қаріптер, кластар, блоктар"),
    ("web", 4): ("Flexbox: блоки в ряд, галерея", "Flexbox: қатардағы блоктар, галерея"),
    ("web", 5): ("формы, кнопки, наведение, тени", "формалар, батырмалар, меңзеу, көлеңкелер"),
    ("web", 6): ("структура, телефон, анимации, свой сайт", "құрылым, телефон, анимациялар, өз сайтың"),
    ("js", 1): ("console.log, переменные, input", "console.log, айнымалылар, input"),
    ("js", 2): ("if, else if, &&, ||, викторина", "if, else if, &&, ||, викторина"),
    ("js", 3): ("for, while, строки", "for, while, жолдар"),
    ("js", 4): ("функции, массивы, игра", "функциялар, массивтер, ойын"),
    ("sql", 1): ("SELECT, WHERE, LIKE", "SELECT, WHERE, LIKE"),
    ("sql", 2): ("ORDER BY, COUNT, AVG, DISTINCT", "ORDER BY, COUNT, AVG, DISTINCT"),
    ("sql", 3): ("GROUP BY, HAVING, JOIN", "GROUP BY, HAVING, JOIN"),
    ("sql", 4): ("INSERT, UPDATE, DELETE, библиотека", "INSERT, UPDATE, DELETE, кітапхана"),
    ("js", 5): ("map, filter, reduce, журнал", "map, filter, reduce, журнал"),
    ("js", 6): ("объекты, магазин", "объектілер, дүкен"),
    ("js", 7): ("Math, вложенные циклы, шифр", "Math, ішкі циклдер, шифр"),
    ("js", 8): ("рекурсия, сортировка, игра", "рекурсия, сұрыптау, ойын"),
    ("sql", 5): ("IN, BETWEEN, NULL, CASE", "IN, BETWEEN, NULL, CASE"),
    ("sql", 6): ("текст, числа, рейтинг", "мәтін, сандар, рейтинг"),
    ("sql", 7): ("LEFT JOIN, подзапросы, продажи", "LEFT JOIN, ішкі сұраулар, сатылым"),
    ("sql", 8): ("CREATE, ALTER, отчёт магазина", "CREATE, ALTER, дүкен есебі"),
    ("word", 1): ("текст, шрифт, абзацы", "мәтін, қаріп, абзацтар"),
    ("word", 2): ("списки, заголовки, таблицы", "тізімдер, тақырыптар, кестелер"),
    ("word", 3): ("картинки, страница, колонтитулы", "суреттер, бет, колонтитулдар"),
    ("word", 4): ("оглавление, сноски, буклет", "мазмұн, сілтемелер, буклет"),
    ("excel", 1): ("ячейки, оформление, форматы", "ұяшықтар, безендіру, пішімдер"),
    ("excel", 2): ("формулы, СУММ, СРЗНАЧ, $", "формулалар, СУММ, СРЗНАЧ, $"),
    ("excel", 3): ("ЕСЛИ, сортировка, фильтр", "ЕСЛИ, сұрыптау, сүзгі"),
    ("excel", 4): ("диаграммы, листы, бюджет", "диаграммалар, парақтар, бюджет"),
    ("powerpoint", 1): ("слайды, списки, дизайн", "слайдтар, тізімдер, дизайн"),
    ("powerpoint", 2): ("картинки, SmartArt, диаграммы", "суреттер, SmartArt, диаграммалар"),
    ("powerpoint", 3): ("переходы, анимация, ссылки", "ауысулар, анимация, сілтемелер"),
    ("powerpoint", 4): ("заметки, правила, проект", "жазбалар, ережелер, жоба"),
}


def module_style(course, number, lang):
    color = MODULE_COLORS[(number - 1) % len(MODULE_COLORS)]
    ru, kk = MODULE_DESC.get((course.slug, number), ("", ""))
    return color, (kk if lang == "kk" and kk else ru)


def _course_map(user, course, lang):
    """Модули курса с уроками, прогрессом, замками и итоговыми тестами."""
    progress = services.lesson_progress(user)
    locks = services.lesson_locks(user, progress)
    results = {}
    if user.is_authenticated:
        results = {r.module_id: r for r in ModuleTestResult.objects.filter(user=user, module__course=course)}
    modules, flat = [], []
    for m in Module.objects.filter(course=course).prefetch_related("lessons"):
        color, desc = module_style(course, m.number, lang)
        lessons = []
        for l in m.lessons.all():
            p = progress.get(l.id, {"solved": 0, "total": 0})
            state = "done" if p["total"] and p["solved"] == p["total"] else ("part" if p["solved"] else "todo")
            lock = locks.get(l.id)
            item = {"lesson": l, "title": l.title(lang), "goal": l.goal(lang), "progress": p, "state": state,
                    "module": m, "color": color, "locked": lock is not None,
                    "lock_test": lock[1] if lock and lock[0] == "test" else None,
                    "lock_paid": bool(lock and lock[0] == "paid")}
            lessons.append(item)
            flat.append(item)
        done = sum(1 for i in lessons if i["state"] == "done")
        lessons_done = bool(lessons) and done == len(lessons)
        test = None
        if m.test:
            r = results.get(m.id)
            test = {"n": len(m.test), "need": m.pass_score, "result": r, "passed": bool(r and r.passed),
                    "available": lessons_done or bool(getattr(user, "is_staff", False))}
        modules.append({"module": m, "title": m.title(lang), "lessons": lessons, "color": color, "desc": desc,
                        "locked": bool(lessons) and lessons[0]["locked"], "test": test,
                        "complete": lessons_done and (test is None or test["passed"]),
                        "done": done, "total": len(lessons), "steps": [k < done for k in range(len(lessons))]})
    return modules, flat


def lessons_word(n, lang):
    """1 урок, 2 урока, 5 уроков; по-казахски всегда «сабақ»."""
    if lang == "kk":
        return "сабақ"
    if n % 10 == 1 and n % 100 != 11:
        return "урок"
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return "урока"
    return "уроков"


def _course(slug):
    return get_object_or_404(Course, slug=slug)


def home(request):
    """Выбор курса."""
    lang = get_lang(request)
    progress = services.lesson_progress(request.user)
    passed = services.passed_module_tests(request.user)
    with_test = services.modules_with_test()
    courses = []
    for c in Course.objects.all():
        ids = list(c.lessons.values_list("id", flat=True))
        done = sum(1 for i in ids if progress.get(i, {}).get("total") and
                   progress[i]["solved"] >= progress[i]["total"])
        tests_ok = set(c.modules.filter(id__in=with_test).values_list("id", flat=True)) <= passed
        courses.append({"course": c, "title": c.title(lang), "desc": c.desc(lang), "lessons": len(ids), "done": done,
                        "lessons_word": lessons_word(len(ids), lang),
                        "complete": bool(ids) and done == len(ids) and tests_ok})
    return render(request, "course/courses.html", {
        "courses": courses, "ct": course_texts(lang), "points": services.user_points(request.user),
    })


def course_home(request, course):
    lang = get_lang(request)
    course = _course(course)
    modules, flat = _course_map(request.user, course, lang)
    next_item = next((i for i in flat if i["state"] != "done" and not i["locked"]), None)
    # тест модуля, который уже можно сдавать, важнее уроков следующих модулей
    next_test = next((m for m in modules if m["test"] and m["test"]["available"] and not m["test"]["passed"]
                      and not request.user.is_staff), None)
    if next_test and next_item and next_item["module"].number <= next_test["module"].number:
        next_test = None
    return render(request, "course/home.html", {
        "course": course, "course_title": course.title(lang), "course_desc": course.desc(lang),
        "modules": modules, "ct": course_texts(lang), "points": services.user_points(request.user),
        "next_item": next_item, "next_test": next_test,
        "need_pay": next_item is None and any(i["lock_paid"] for i in flat), "started": any(i["progress"]["solved"] for i in flat),
        "complete": bool(flat) and all(m["complete"] for m in modules),
        "cert": Certificate.objects.filter(user=request.user, course=course).first() if request.user.is_authenticated else None,
    })


def module_detail(request, course, number):
    lang = get_lang(request)
    course = _course(course)
    modules, _ = _course_map(request.user, course, lang)
    mod = next((m for m in modules if m["module"].number == number), None)
    if mod is None:
        raise Http404
    ct = course_texts(lang)
    rule = ct["test_rule"].format(n=mod["test"]["n"], need=mod["test"]["need"]) if mod["test"] else ""
    return render(request, "course/module.html", {"course": course, "course_title": course.title(lang),
                                                  "m": mod, "ct": ct, "rule": rule,
                                                  "points": services.user_points(request.user)})


def _pick(v, lang):
    """Строка или пара (ru, kk) → текст на нужном языке."""
    if isinstance(v, (list, tuple)):
        return v[1] if lang == "kk" and len(v) > 1 and v[1] else v[0]
    return v


def module_test(request, course, number):
    """Итоговый тест модуля: 20 вопросов, нужно 18 верных. Порядок вопросов и вариантов
    перемешивается на каждой попытке; правильные ответы хранятся только на сервере."""
    lang = get_lang(request)
    ct = course_texts(lang)
    course = _course(course)
    module = get_object_or_404(Module, course=course, number=number)
    if not module.test:
        raise Http404
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    if not services.module_lessons_done(request.user, module) and not request.user.is_staff:
        messages.info(request, ct["test_not_yet"])
        return redirect("course_module", course.slug, number)

    key = f"module_test_{module.id}"
    color, _ = module_style(course, number, lang)
    ctx = {"course": course, "course_title": course.title(lang), "module": module, "module_title": module.title(lang),
           "ct": ct, "color": color, "points": services.user_points(request.user),
           "need": module.pass_score, "n": len(module.test),
           "rule": ct["test_rule"].format(n=len(module.test), need=module.pass_score),
           "lose": ct["test_lose"].format(n=len(module.test), need=module.pass_score)}

    if request.method == "POST":
        attempt = request.session.get(key)
        if not attempt:  # попытка устарела (например, открыта в другой вкладке)
            messages.info(request, ct["test_expired"])
            return redirect("course_module_test", course.slug, number)
        rows, score = [], 0
        for pos, (qi, perm) in enumerate(zip(attempt["order"], attempt["perm"])):
            q = module.test[qi]
            raw = request.POST.get(f"q{pos}")
            chosen = perm[int(raw)] if raw is not None and raw.isdigit() and int(raw) < len(perm) else None
            ok = chosen == q["answer"]
            score += ok
            rows.append({"num": pos + 1, "ok": ok, "text": _pick(q["q"], lang), "code": q.get("code", ""),
                         "picked": _pick(q["options"][chosen], lang) if chosen is not None else ""})
        del request.session[key]
        result = services.record_module_test(request.user, module, score)
        next_module = Module.objects.filter(course=course, number__gt=number).order_by("number").first()
        ctx.update({"score": score, "rows": rows, "passed_now": score >= module.pass_score, "result": result,
                    "next_module": next_module, "next_module_title": next_module.title(lang) if next_module else ""})
        return render(request, "course/module_test_result.html", ctx)

    import random
    rnd = random.SystemRandom()
    order = list(range(len(module.test)))
    rnd.shuffle(order)
    perm = []
    questions = []
    for pos, qi in enumerate(order):
        q = module.test[qi]
        p = list(range(len(q["options"])))
        rnd.shuffle(p)
        perm.append(p)
        questions.append({"num": pos + 1, "name": f"q{pos}", "text": _pick(q["q"], lang), "code": q.get("code", ""),
                          "options": [{"value": i, "text": _pick(q["options"][oi], lang)} for i, oi in enumerate(p)]})
    request.session[key] = {"order": order, "perm": perm}
    ctx.update({"questions": questions,
                "result": ModuleTestResult.objects.filter(user=request.user, module=module).first()})
    return render(request, "course/module_test.html", ctx)


def _quiz_options(task, lang):
    if task.kind != Task.Kind.QUIZ or not task.tests:
        return []
    out = []
    for o in task.tests[0].get("options", []):
        ru, kk = (o[0], o[1] if len(o) > 1 and o[1] else o[0]) if isinstance(o, list) else (o, o)
        out.append(kk if lang == "kk" else ru)
    return out


def lesson_detail(request, course, number):
    lang = get_lang(request)
    course = _course(course)
    lesson = get_object_or_404(Lesson.objects.select_related("module"), course=course, number=number)
    ct = course_texts(lang)
    lock = services.lesson_lock(request.user, lesson)
    if lock:
        if lock[0] == "paid":
            messages.info(request, ct["locked_paid_msg"])
            return redirect("pay")
        if lock[0] == "test":
            messages.info(request, ct["locked_test_msg"].format(n=lock[1]))
            return redirect("course_module", course.slug, lock[1])
        if request.user.is_authenticated:
            messages.info(request, f"{ct['locked_msg']} {number - 1}.")
        else:
            messages.info(request, ct["locked_guest"])
        return redirect("course_module", course.slug, lesson.module.number)
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
            "example_input": (t.tests[0].get("input", "") if t.tests and t.kind not in
                              (Task.Kind.WEB, Task.Kind.QUIZ, Task.Kind.FILE) else ""),
            # JSON для страницы; "<" экранируем, чтобы код вроде "</script>" не ломал HTML
            "data_json": json.dumps({"tests": [] if t.kind in (Task.Kind.QUIZ, Task.Kind.FILE) else t.tests,
                                     "starter": t.starter_code}, ensure_ascii=False).replace("<", "\\u003c"),
            "options": _quiz_options(t, lang),
            "picked": s.code if s and t.kind == Task.Kind.QUIZ else "",
        })
    color, _ = module_style(course, lesson.module.number, lang)
    prev_lesson = Lesson.objects.filter(course=course, number__lt=number).order_by("-number").first()
    next_lesson = Lesson.objects.filter(course=course, number__gt=number).order_by("number").first()
    return render(request, "course/lesson.html", {
        "course": course, "lesson": lesson, "title": lesson.title(lang), "goal": lesson.goal(lang),
        "module_title": lesson.module.title(lang), "theory": lesson.theory_blocks(lang),
        "tasks": tasks, "prev": prev_lesson, "next": next_lesson, "ct": ct,
        "pyodide_url": settings.PYODIDE_URL, "color": color,
        "points": services.user_points(request.user),
        "next_title": next_lesson.title(lang) if next_lesson else "",
        "lesson_done": bool(tasks) and all(t["solved"] for t in tasks),
        "is_teacher": request.user.is_staff,
        "file_ext": office_checks.EXT.get(course.kind, ""),
    })


def legacy_lesson(request, number):
    """Старые адреса /lesson/5/ ведут в курс Python."""
    return redirect("course_lesson", "python", number, permanent=True)


def legacy_module(request, number):
    return redirect("course_module", "python", number, permanent=True)


def _check_quiz(request, task):
    try:
        choice = int(json.loads(request.body or "{}").get("choice"))
    except (json.JSONDecodeError, TypeError, ValueError):
        return None, None, None
    answer = task.tests[0].get("answer") if task.tests else None
    options = task.tests[0].get("options", []) if task.tests else []
    if not 0 <= choice < len(options):
        return None, None, None
    picked = options[choice][0] if isinstance(options[choice], list) else options[choice]
    return int(choice == answer), 1, {"correct": choice == answer, "code": picked}


def _check_office_file(request, task, lang):
    f = request.FILES.get("file")
    ext = office_checks.EXT.get(task.lesson.course.kind, "")
    ct = course_texts(lang)
    if f is None:
        return None, None, {"error": ct["file_missing"]}
    if f.size > office_checks.MAX_SIZE:
        return None, None, {"error": ct["file_too_big"]}
    if not f.name.lower().endswith(ext):
        return None, None, {"error": f"{ct['file_wrong_ext']} {ext}"}
    results, error = office_checks.check_file(task.lesson.course.kind, f.read(), task.tests, lang)
    if error:
        return None, None, {"error": error}
    passed = sum(r["ok"] for r in results)
    return passed, len(results), {"results": results, "code": f"[файл] {f.name}: {passed} из {len(results)}"}


@require_POST
def submit(request, task_id):
    task = get_object_or_404(Task.objects.select_related("lesson", "lesson__course"), pk=task_id)
    server_checked = task.kind in (Task.Kind.QUIZ, Task.Kind.FILE)
    if not request.user.is_authenticated and not server_checked:
        return redirect_to_login(request.get_full_path())
    if not services.is_lesson_open(request.user, task.lesson):
        return JsonResponse({"ok": False, "error": "locked"}, status=403)

    if server_checked:  # тесты и файлы проверяет сервер - клиенту не доверяем
        lang = get_lang(request)
        if task.kind == Task.Kind.QUIZ:
            passed, total, extra = _check_quiz(request, task)
        else:
            passed, total, extra = _check_office_file(request, task, lang)
        if passed is None:
            if extra and "error" in extra:
                return JsonResponse({"ok": False, "error": extra["error"]}, status=400)
            return JsonResponse({"ok": False, "error": "bad request"}, status=400)
        code = extra.pop("code", "")
        out = {"ok": True, "passed": passed, "total": total, "solved": passed == total, **extra}
        if request.user.is_authenticated:
            sub = services.record_submission(request.user, task, code, passed, total)
            out["solved_ever"] = sub.solved
        return JsonResponse(out)

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
    courses = list(Course.objects.all())
    if not courses:
        raise Http404
    current = next((c for c in courses if c.slug == request.GET.get("course")), courses[0])
    lessons, rows = services.group_progress(current)
    return render(request, "course/progress.html", {
        "lessons": lessons, "rows": rows, "ct": course_texts(lang),
        "courses": [{"course": c, "title": c.title(lang)} for c in courses], "current": current,
    })
