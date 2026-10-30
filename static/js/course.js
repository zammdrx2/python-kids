/*
 * Курс Python: редактор, запуск и автопроверка кода в браузере.
 * Код выполняется в Web Worker (pyworker.js) с Pyodide.
 */
(function () {
  const root = document.getElementById("lesson");
  if (!root) return;

  const T = JSON.parse(document.getElementById("course-texts").textContent);
  const LANG = root.dataset.lang;
  const INDEX_URL = root.dataset.pyodide;
  const WORKER_URL = root.dataset.worker;
  const CSRF = root.dataset.csrf;
  const LOGGED_IN = root.dataset.auth === "1";
  const RUN_TIMEOUT = 5000;    // мс на один запуск
  const LOAD_TIMEOUT = 60000;  // мс на загрузку Python

  // ---------- Worker ----------
  let worker = null, ready = null, seq = 0;
  const pending = new Map();

  function startWorker() {
    worker = new Worker(WORKER_URL);
    worker.onmessage = (e) => {
      const p = pending.get(e.data.id);
      if (p) { clearTimeout(p.timer); pending.delete(e.data.id); p.resolve(e.data); }
    };
    ready = call({ type: "init", indexURL: INDEX_URL }, LOAD_TIMEOUT);
    return ready;
  }

  function call(msg, timeout) {
    return new Promise((resolve) => {
      const id = ++seq;
      const timer = setTimeout(() => {
        pending.delete(id);
        worker.terminate();          // останавливаем зависшую программу
        worker = null; ready = null;
        resolve({ ok: false, timeout: true });
      }, timeout);
      pending.set(id, { resolve, timer });
      worker.postMessage({ id, indexURL: INDEX_URL, ...msg });
    });
  }

  async function runPython(code, inputs, showPrompt) {
    if (!worker) startWorker();
    const init = await ready;
    if (!init || !init.ok) return init || { ok: false, fatal: "init failed" };
    return call({ type: "run", code, inputs, showPrompt }, RUN_TIMEOUT);
  }

  // ---------- Подсказки по ошибкам для детей ----------
  const ERROR_HINTS = {
    ru: {
      SyntaxError: "Ошибка в записи программы: проверьте скобки, кавычки и двоеточие после if / for / while / def.",
      IndentationError: "Неправильный отступ. Строки внутри if, for, while и def сдвигаются на 4 пробела.",
      NameError: "Python не знает такое имя. Проверьте, нет ли опечатки и создана ли переменная до использования.",
      TypeError: "Действие с неподходящими типами: например, строку нельзя сложить с числом. Может, нужно int() или str()?",
      ValueError: "Неподходящее значение: например, int() не может превратить в число текст с буквами.",
      ZeroDivisionError: "Деление на ноль невозможно.",
      IndexError: "Обращение к элементу, которого нет: индексы начинаются с 0 и заканчиваются на len() - 1.",
      EOFError: "Программа вызвала input() больше раз, чем есть входных данных.",
      KeyError: "В словаре нет такого ключа.",
    },
    kk: {
      SyntaxError: "Бағдарлама жазылуында қате бар: жақшаларды, тырнақшаларды және if / for / while / def кейінгі қос нүктені тексеріңіз.",
      IndentationError: "Шегініс дұрыс емес. if, for, while және def ішіндегі жолдар 4 бос орынға жылжиды.",
      NameError: "Python мұндай атауды білмейді. Қате жазылмағанын және айнымалы алдын ала құрылғанын тексеріңіз.",
      TypeError: "Сәйкес келмейтін типтермен әрекет: мысалы, жолды санға қосуға болмайды. Мүмкін, int() немесе str() керек шығар?",
      ValueError: "Мән сәйкес емес: мысалы, int() әріптері бар мәтінді санға айналдыра алмайды.",
      ZeroDivisionError: "Нөлге бөлуге болмайды.",
      IndexError: "Жоқ элементке жүгіну: индекстер 0-ден басталып, len() - 1-де аяқталады.",
      EOFError: "Бағдарлама input()-ты кіріс деректерден көп рет шақырды.",
      KeyError: "Сөздікте мұндай кілт жоқ.",
    },
  };

  // ---------- Вспомогательные функции ----------
  const normalize = (s) => s.replace(/\r/g, "").split("\n").map((l) => l.replace(/\s+$/, "")).join("\n").replace(/\n+$/, "");
  const splitInput = (s) => (s === "" ? [] : s.replace(/\r/g, "").replace(/\n$/, "").split("\n"));

  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function showError(box, error) {
    box.appendChild(el("pre", "out out--error", error.text));
    const hint = (ERROR_HINTS[LANG] || ERROR_HINTS.ru)[error.type];
    if (hint) box.appendChild(el("p", "err-hint", "💡 " + hint));
  }

  function showFatal(box, res) {
    box.appendChild(el("p", "out--error", res.timeout ? T.timeout : "Python: " + (res.fatal || "error")));
  }

  async function save(card, code, passed) {
    if (!LOGGED_IN) return null;
    try {
      const r = await fetch(card.dataset.submit, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF },
        body: JSON.stringify({ code, passed }),
      });
      return await r.json();
    } catch (e) {
      return { ok: false };
    }
  }

  function markSolved(card) {
    card.classList.add("is-solved");
    const badge = card.querySelector(".task__badge");
    if (badge) badge.hidden = false;
  }

  // ---------- Задания ----------
  document.querySelectorAll(".task").forEach((card) => {
    const editor = card.querySelector("textarea.editor");
    const inputBox = card.querySelector("textarea.stdin");
    const out = card.querySelector(".task__out");
    const data = JSON.parse(card.querySelector("script.taskdata").textContent);
    const tests = data.tests;
    const starter = data.starter;
    const kind = card.dataset.kind;

    // Tab вставляет 4 пробела, Enter сохраняет отступ строки
    editor.addEventListener("keydown", (e) => {
      if (e.key === "Tab") {
        e.preventDefault();
        editor.setRangeText("    ", editor.selectionStart, editor.selectionEnd, "end");
      } else if (e.key === "Enter") {
        const before = editor.value.slice(0, editor.selectionStart);
        const line = before.split("\n").pop();
        let indent = line.match(/^\s*/)[0];
        if (/:\s*$/.test(line)) indent += "    ";
        e.preventDefault();
        editor.setRangeText("\n" + indent, editor.selectionStart, editor.selectionEnd, "end");
      }
    });

    card.querySelector(".js-reset")?.addEventListener("click", () => {
      if (confirm(T.reset_confirm)) editor.value = starter;
    });

    // ▶ Запустить
    card.querySelector(".js-run").addEventListener("click", async () => {
      out.replaceChildren(el("p", "muted", worker ? T.running : T.loading_python));
      const res = await runPython(editor.value, splitInput(inputBox.value), true);
      out.replaceChildren(el("p", "out__label", T.output));
      if (!res.ok) return showFatal(out, res);
      out.appendChild(el("pre", "out", res.stdout || T.no_output));
      if (res.error) showError(out, res.error);
      card.dataset.ranOk = res.error ? "" : "1";
    });

    // ✓ Проверить / Сдать проект
    card.querySelector(".js-check").addEventListener("click", async () => {
      const code = editor.value;
      if (kind === "project") {
        if (!code.trim() || code.trim() === starter.trim()) {
          out.replaceChildren(el("p", "out--error", T.project_need_code));
          return;
        }
        const r = await save(card, code, 1);
        out.replaceChildren(el("p", "out--ok", r && r.ok ? T.project_saved : (LOGGED_IN ? T.save_error : T.login_to_save)));
        if (r && r.solved) markSolved(card);
        return;
      }

      out.replaceChildren(el("p", "muted", worker ? T.checking : T.loading_python));
      let passed = 0;
      const results = el("ol", "tests");
      for (let i = 0; i < tests.length; i++) {
        const t = tests[i];
        const res = await runPython(code, splitInput(t.input), false);
        const li = el("li", "test");
        const ok = res.ok && !res.error && normalize(res.stdout) === normalize(t.output);
        passed += ok;
        li.classList.add(ok ? "test--ok" : "test--fail");
        li.appendChild(el("span", "test__title", `${T.test} ${i + 1}: ${ok ? "✓ " + T.passed : "✗ " + T.failed}`));
        if (!ok) {
          if (t.input) { li.appendChild(el("span", "test__label", T.given_input)); li.appendChild(el("pre", "out", t.input)); }
          li.appendChild(el("span", "test__label", T.expected)); li.appendChild(el("pre", "out", t.output));
          li.appendChild(el("span", "test__label", T.got));
          if (!res.ok) showFatal(li, res);
          else {
            li.appendChild(el("pre", "out", res.stdout || T.no_output));
            if (res.error) showError(li, res.error);
          }
        }
        results.appendChild(li);
        if (!ok && !res.ok) break;  // зависание: дальше не проверяем
      }
      const summary = passed === tests.length
        ? el("p", "out--ok", "🎉 " + T.all_passed)
        : el("p", "out--error", `${T.some_failed}: ${passed} / ${tests.length}`);
      out.replaceChildren(summary, results);
      const r = await save(card, code, passed);
      if (!LOGGED_IN) out.appendChild(el("p", "muted", T.login_to_save));
      else if (!r || !r.ok) out.appendChild(el("p", "out--error", T.save_error));
      if (passed === tests.length || (r && r.solved)) markSolved(card);
    });
  });

  // Заранее загружаем Python, пока ученик читает теорию
  if (document.querySelector(".task")) setTimeout(() => { if (!worker) startWorker(); }, 1500);
})();
