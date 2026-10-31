"""Собирает course/data/course.json из part1.py и part2.py и проверяет эталонные решения.

    python course/data/build/build.py
"""
import builtins
import contextlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from part1 import MODULES as M1  # noqa: E402
from part2 import MODULES as M2  # noqa: E402
from part3 import EXTRA  # noqa: E402


def normalize(s):
    return "\n".join(line.rstrip() for line in s.replace("\r", "").split("\n")).rstrip("\n")


def run(code, inp):
    lines = inp.split("\n") if inp else []
    it = iter(lines)
    out = io.StringIO()

    def _input(prompt=""):
        return next(it)

    with contextlib.redirect_stdout(out):
        exec(compile(code, "<solution>", "exec"), {"__name__": "__main__", "input": _input, "__builtins__": builtins})
    return out.getvalue()


def main():
    modules = M1 + M2
    # дополнительные задания встают перед свободным проектом урока
    for m in modules:
        for lesson in m["lessons"]:
            extra = EXTRA.get(lesson["number"], [])
            tasks = lesson["tasks"]
            pos = next((k for k, t in enumerate(tasks) if t.get("kind") == "project"), len(tasks))
            lesson["tasks"] = tasks[:pos] + extra + tasks[pos:]
            # ожидаемый вывод, если не указан, получаем из эталонного решения
            for t in extra:
                for test in t["tests"]:
                    if "output" not in test:
                        test["output"] = normalize(run(t["solution"], test["input"]))
    errors, n_tests, n_lessons = [], 0, 0
    numbers = []
    for m in modules:
        for lesson in m["lessons"]:
            n_lessons += 1
            numbers.append(lesson["number"])
            for i, t in enumerate(lesson["tasks"], 1):
                if t.get("kind", "tested") != "tested":
                    continue
                for j, test in enumerate(t["tests"], 1):
                    n_tests += 1
                    try:
                        got = run(t["solution"], test["input"])
                    except Exception as e:  # noqa: BLE001
                        errors.append(f"урок {lesson['number']} задание {i} тест {j}: {type(e).__name__}: {e}")
                        continue
                    if normalize(got) != normalize(test["output"]):
                        errors.append(f"урок {lesson['number']} задание {i} тест {j}: ожидалось {test['output']!r}, получено {got!r}")
    assert numbers == list(range(1, 25)), numbers
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    out = HERE.parent / "course.json"
    course = {"slug": "python", "kind": "python", "title": ["Python", "Python"],
              "desc": ["24 урока: от первой программы до своей игры", "24 сабақ: алғашқы бағдарламадан өз ойыныңа дейін"],
              "color": "#FFD166", "order": 1}
    out.write_text(json.dumps({"course": course, "modules": modules}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK: уроков {n_lessons}, тестов {n_tests} — все эталоны проходят. Записано {out}")


if __name__ == "__main__":
    main()
