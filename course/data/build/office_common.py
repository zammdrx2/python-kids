"""
Общие помощники для курсов Word, Excel и PowerPoint.

Урок = теория + 4 теста (Q) + 2 практических задания с файлом (F).
build() проверяет, что у теста есть верный ответ, а для каждого задания с файлом
эталонный файл проходит все проверки, а пустой - нет; затем пишет JSON курса.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2]))

from office_make import make_blank, make_solution  # noqa: E402

from course.office_checks import check_file  # noqa: E402


def Q(ru, kk, options, answer):
    """Тест: вопрос, варианты [(ru, kk), ...], номер правильного (с нуля).
    Варианты перемешиваются (всегда одинаково для одного вопроса), чтобы верный не стоял всегда первым."""
    import hashlib
    import random
    opts = [list(o) for o in options]
    right = opts[answer]
    random.Random(int(hashlib.md5(ru.encode()).hexdigest(), 16)).shuffle(opts)
    return {"kind": "quiz", "text": [ru, kk], "tests": [{"options": opts, "answer": opts.index(right)}],
            "points": 5}


def F(title, text, checks, hint=("", "")):
    """Практика: ученик делает файл и загружает его. title/text/hint - пары (ru, kk)."""
    return {"kind": "file", "title": list(title), "text": list(text), "hint": list(hint), "tests": checks,
            "points": 15}


def lesson(number, title, goal, theory, tasks, project=False):
    q = 0
    for t in tasks:
        if t["kind"] == "quiz":
            q += 1
            t["title"] = [f"Вопрос {q}", f"{q}-сұрақ"]
    return {"number": number, "title": list(title), "goal": list(goal),
            "theory": [{"p": list(p)} for p in theory], "tasks": tasks, "project": project}


def module(number, title, lessons):
    return {"number": number, "title": list(title), "lessons": lessons}


def build(course, modules, kind, out_name):
    n_quiz = n_file = 0
    for m in modules:
        for l in m["lessons"]:
            for i, t in enumerate(l["tasks"], 1):
                where = f"урок {l['number']}, задание {i}"
                if t["kind"] == "quiz":
                    opts, ans = t["tests"][0]["options"], t["tests"][0]["answer"]
                    assert 0 <= ans < len(opts) and len(opts) >= 3, where
                    assert all(len(o) == 2 and o[0] and o[1] for o in opts), where
                    assert len({o[0] for o in opts}) == len(opts), f"{where}: одинаковые варианты"
                    n_quiz += 1
                else:
                    res, err = check_file(kind, make_solution(kind, t["tests"]), t["tests"])
                    assert not err, f"{where}: {err}"
                    bad = [r["msg"] for r in res if not r["ok"]]
                    assert not bad, f"{where}: эталон не прошёл {bad}"
                    res, err = check_file(kind, make_blank(kind), t["tests"])
                    assert not all(r["ok"] for r in res), f"{where}: пустой файл проходит все проверки"
                    for lang in ("ru", "kk"):
                        check_file(kind, make_solution(kind, t["tests"]), t["tests"], lang)
                    n_file += 1
    data = {"course": course, "modules": modules}
    path = HERE.parent / out_name
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    n_lessons = sum(len(m["lessons"]) for m in modules)
    print(f"{course['title'][0]}: уроков {n_lessons}, тестов {n_quiz}, заданий с файлом {n_file} → {path.name}")
