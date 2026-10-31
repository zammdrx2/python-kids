"""
Загрузка курсов:  python manage.py load_course [путь]
Без пути загружаются все курсы из course/data/*.json.

Формат файла: {"course": {"slug": "python", "kind": "python", "title": [...], "desc": [...],
"color": "#FFD166", "order": 1}, "modules": [...]}. Старый формат — просто список модулей
(тогда это курс Python). Модули:
[
  {"number": 1, "title": ["рус", "қаз"], "lessons": [
    {"number": 1, "title": [...], "goal": [...], "project": false,
     "theory": [{"p": ["абзац", "абзац қаз"]}, {"code": "print('Привет')"}],
     "tasks": [
       {"title": [...], "text": [...], "hint": [...], "starter": "", "solution": "...",
        "tests": [{"input": "", "output": "..."}], "points": 10},
       {"kind": "project", "title": [...], "text": [...], "starter": "..."}
     ]}
  ]}
]
Повторный запуск обновляет тексты и тесты, не удаляя решения учеников.
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from course.models import Course, Lesson, Module, Task

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PYTHON_DEFAULT = {"slug": "python", "kind": "python", "title": ["Python", "Python"], "color": "#FFD166", "order": 1}


def pair(v):
    if isinstance(v, str):
        return v, ""
    return v[0], (v[1] if len(v) > 1 else "")


class Command(BaseCommand):
    help = "Загружает уроки и задания курса Python"

    def add_arguments(self, parser):
        parser.add_argument("path", nargs="?", default=None)

    def handle(self, *args, path, **options):
        paths = [Path(path)] if path else sorted(DATA_DIR.glob("*.json"))
        for p in paths:
            self.load_file(p)

    @transaction.atomic
    def load_file(self, path):
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Не удалось прочитать {path}: {exc}")
        if isinstance(data, list):
            data = {"course": PYTHON_DEFAULT, "modules": data}
        c = data["course"]
        cru, ckk = pair(c.get("title", c["slug"]))
        dru, dkk = pair(c.get("desc", ""))
        course, _ = Course.objects.update_or_create(slug=c["slug"], defaults={
            "kind": c.get("kind", "python"), "title_ru": cru, "title_kk": ckk, "desc_ru": dru, "desc_kk": dkk,
            "color": c.get("color", "#FFD166"), "order": c.get("order", 0),
        })

        n_lessons = n_tasks = 0
        for m in data["modules"]:
            ru, kk = pair(m["title"])
            module, _ = Module.objects.update_or_create(course=course, number=m["number"],
                                                        defaults={"title_ru": ru, "title_kk": kk})
            for l in m["lessons"]:
                tru, tkk = pair(l["title"])
                gru, gkk = pair(l.get("goal", ""))
                lesson, _ = Lesson.objects.update_or_create(course=course, number=l["number"], defaults={
                    "module": module, "title_ru": tru, "title_kk": tkk, "goal_ru": gru, "goal_kk": gkk,
                    "theory": l.get("theory", []), "is_project": l.get("project", False),
                })
                n_lessons += 1
                keep = []
                for order, t in enumerate(l.get("tasks", []), start=1):
                    kind = t.get("kind", {"web": "web", "js": "js", "sql": "sql"}.get(course.kind, "tested"))
                    if kind != "project" and not t.get("tests"):
                        raise CommandError(f"Урок {l['number']}, задание {order}: нет тестов")
                    a, b = pair(t["title"]); c, d = pair(t["text"]); e, f = pair(t.get("hint", ""))
                    task, _ = Task.objects.update_or_create(lesson=lesson, order=order, defaults={
                        "kind": kind, "title_ru": a, "title_kk": b, "text_ru": c, "text_kk": d,
                        "hint_ru": e, "hint_kk": f, "starter_code": t.get("starter", ""),
                        "tests": t.get("tests", []), "solution": t.get("solution", ""),
                        "points": t.get("points", 15 if kind == "project" else 10),
                    })
                    keep.append(task.id)
                    n_tasks += 1
                lesson.tasks.exclude(id__in=keep).delete()

        self.stdout.write(self.style.SUCCESS(f"Курс «{cru}» загружен: уроков {n_lessons}, заданий {n_tasks}"))
