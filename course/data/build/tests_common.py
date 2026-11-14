"""
Общая сборка итоговых тестов модулей (HTML/CSS, JavaScript, SQL).

Вопрос: Q(текст_ru, текст_kk, варианты, номер_верного, code="...", out=None, run=True, err=False)
  варианты - строки (одинаковые на обоих языках) или пары (ru, kk);
  run  - код запускается тем же движком, что и на сайте, и его вывод должен
         совпасть с правильным вариантом (или с out);
  err  - код должен завершиться ошибкой.
Каждый модуль - ровно 20 вопросов по 4 варианта.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = Path(__file__).resolve().parents[1] / "module_tests"


def Q(ru, kk, options, answer, code="", out=None, run=True, err=False, exec_code=None):
    return {"q": [ru, kk], "code": code.strip("\n"), "options": options, "answer": answer,
            "out": out, "run": run and bool(code) and not err, "err": err,
            "exec": (exec_code if exec_code is not None else code).strip("\n")}


def opt_text(o):
    return o if isinstance(o, str) else o[0]


def node_run(script: str, codes: list[str]) -> list[dict]:
    """Запускает в Node все фрагменты сразу; script читает JSON со списком кодов из argv[2]."""
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "codes.json"
        src.write_text(json.dumps(codes, ensure_ascii=False), encoding="utf-8")
        res = subprocess.run(["node", "-e", script, "--", str(src), str(ROOT)],
                             capture_output=True, text=True, timeout=300)
        if res.returncode:
            raise SystemExit(res.stderr)
        return json.loads(res.stdout)


def build(name: str, slug: str, modules: dict, runner=None):
    """runner(список кодов) -> список {"out": str} или {"error": str}."""
    todo = [(n, i, q) for n, qs in modules.items() for i, q in enumerate(qs, 1) if q["run"] or q["err"]]
    results = runner([q["exec"] for _, _, q in todo]) if todo and runner else []
    got = {(n, i): r for (n, i, _), r in zip(todo, results)}

    data = {}
    for number, qs in modules.items():
        assert len(qs) == 20, f"{name}, модуль {number}: {len(qs)} вопросов, нужно 20"
        seen, out = set(), []
        for i, q in enumerate(qs, 1):
            where = f"{name}, модуль {number}, вопрос {i}"
            opts = [list(o) if not isinstance(o, str) else o for o in q["options"]]
            assert len(opts) == 4, where
            assert len({opt_text(o) for o in opts}) == 4, f"{where}: одинаковые варианты"
            assert 0 <= q["answer"] < 4, where
            assert q["q"][0] and q["q"][1], f"{where}: нет текста"
            key = (q["q"][0], q["code"])
            assert key not in seen, f"{where}: повтор"
            seen.add(key)
            if q["run"]:
                r = got[(number, i)]
                assert "error" not in r, f"{where}: ошибка {r.get('error')}\n{q['exec']}"
                want = q["out"] if q["out"] is not None else opt_text(opts[q["answer"]])
                assert r["out"] == want, f"{where}: код выводит {r['out']!r}, а верный ответ {want!r}\n{q['exec']}"
                if q["out"] is None:
                    for j, o in enumerate(opts):
                        assert j == q["answer"] or opt_text(o) != r["out"], f"{where}: вариант {j} тоже верный"
            elif q["err"]:
                assert "error" in got[(number, i)], f"{where}: ожидалась ошибка, но код работает"
            out.append({"q": q["q"], "code": q["code"], "options": opts, "answer": q["answer"]})
        data[str(number)] = out
    path = OUT_DIR / f"{slug}.json"
    OUT_DIR.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{name}: {sum(len(v) for v in data.values())} вопросов в {len(data)} модулях → {path.name}")
