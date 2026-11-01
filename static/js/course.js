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
  const JS_WORKER_URL = root.dataset.jsworker;
  const SQL_BASE = root.dataset.sqljs;
  const RUN_TIMEOUT = 5000;    // мс на один запуск
  const LOAD_TIMEOUT = 60000;  // мс на загрузку Python

  // ---------- Подсветка кода в теории ----------
  const KW = new Set("False None True and as break continue def del elif else for from if import in is lambda not or pass return while with".split(" "));
  const BI = new Set("print input int float str len range list dict set sum min max abs round sorted enumerate map type bool".split(" "));
  const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  function highlight(src) {
    const re = /(#.*$)|("(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*')|(\b\d+(?:\.\d+)?\b)|([A-Za-z_]\w*)/gm;
    let out = "", last = 0, m;
    while ((m = re.exec(src))) {
      out += esc(src.slice(last, m.index));
      const [tok, com, str, num, word] = m;
      if (com) out += `<span class="tok-com">${esc(tok)}</span>`;
      else if (str) out += `<span class="tok-str">${esc(tok)}</span>`;
      else if (num) out += `<span class="tok-num">${tok}</span>`;
      else if (KW.has(word)) out += `<span class="tok-kw">${tok}</span>`;
      else if (BI.has(word)) out += `<span class="tok-fn">${tok}</span>`;
      else out += esc(tok);
      last = re.lastIndex;
    }
    return out + esc(src.slice(last));
  }
  document.querySelectorAll("pre.js-hl code").forEach((c) => { c.innerHTML = highlight(c.textContent); });

  // ---------- Шаги урока: на экране одна часть (теория или одно задание) ----------
  const panels = Array.from(document.querySelectorAll(".step-panel"));
  const pills = Array.from(document.querySelectorAll(".steps a"));
  function showStep(id, scroll) {
    if (!document.getElementById(id)) id = panels[0].id;
    panels.forEach((p) => {
      p.hidden = p.id !== id;
      const cmEl = p.querySelector(".CodeMirror");
      if (!p.hidden && cmEl && cmEl.CodeMirror) cmEl.CodeMirror.refresh();
    });
    pills.forEach((a) => {
      if (a.hash === "#" + id) a.setAttribute("aria-current", "step");
      else a.removeAttribute("aria-current");
    });
    if (scroll) {
      const nav = document.querySelector(".steps");
      window.scrollTo({ top: Math.max(0, nav.getBoundingClientRect().top + window.scrollY - 12) });
    }
  }
  if (panels.length) {
    showStep(location.hash.slice(1) || panels[0].id, false);
    document.addEventListener("click", (e) => {
      const a = e.target.closest('a[href^="#step-"]');
      if (!a) return;
      e.preventDefault();
      history.replaceState(null, "", a.hash);
      showStep(a.hash.slice(1), true);
    });
    window.addEventListener("hashchange", () => showStep(location.hash.slice(1), true));
  }

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
        if (worker) worker.terminate();  // останавливаем зависшую программу
        worker = null; ready = null;
        resolve({ ok: false, timeout: true });
      }, timeout);
      pending.set(id, { resolve, timer });
      worker.postMessage({ id, indexURL: INDEX_URL, ...msg });
    });
  }

  let busy = 0;
  async function runPython(code, inputs, showPrompt) {
    if (!worker) startWorker();
    busy++;
    try {
      const init = await ready;
      if (!init || !init.ok) return init || { ok: false, fatal: "init failed" };
      return await call({ type: "run", code, inputs, showPrompt }, RUN_TIMEOUT);
    } finally {
      busy--;
    }
  }

  // Проверка записи программы без запуска (для подсветки ошибок во время набора)
  async function lintCode(code) {
    if (!worker || !ready || busy) return undefined;  // не загружаем Python ради проверки
    const init = await ready;
    if (!init || !init.ok || busy) return undefined;
    const res = await call({ type: "lint", code }, 3000);
    return res && res.ok ? res.lint : undefined;
  }

  // ---------- JavaScript: отдельный Worker ----------
  let jsw = null, jsSeq = 0;
  const jsPending = new Map();
  function runJS(code, inputs, showPrompt) {
    if (!jsw) {
      jsw = new Worker(JS_WORKER_URL);
      jsw.onmessage = (e) => {
        const p = jsPending.get(e.data.id);
        if (p) { clearTimeout(p.timer); jsPending.delete(e.data.id); p.resolve(e.data); }
      };
    }
    return new Promise((resolve) => {
      const id = ++jsSeq;
      const timer = setTimeout(() => {
        jsPending.delete(id);
        if (jsw) jsw.terminate();
        jsw = null;
        resolve({ ok: false, timeout: true });
      }, RUN_TIMEOUT);
      jsPending.set(id, { resolve, timer });
      jsw.postMessage({ id, code, inputs, showPrompt });
    });
  }
  function lintJS(code) {
    try { new Function("console", "input", "prompt", "alert", code); return null; } catch (e) {
      return e instanceof SyntaxError ? { type: "SyntaxError", msg: e.message, line: null } : null;
    }
  }

  // ---------- SQL: база SQLite прямо в браузере (sql.js) ----------
  let sqlReady = null;
  function getSQL() {
    if (!sqlReady) sqlReady = window.initSqlJs({ locateFile: (f) => SQL_BASE + f });
    return sqlReady;
  }
  async function runSQL(setup, query, after) {
    let SQL;
    try { SQL = await getSQL(); } catch (e) { return { ok: false, fatal: "SQL: " + e }; }
    const db = new SQL.Database();
    try {
      if (setup) db.run(setup);
      let res;
      if (after) { db.run(query); res = db.exec(after); } else res = db.exec(query);
      const last = res[res.length - 1] || { columns: [], values: [] };
      return { ok: true, columns: last.columns, rows: last.values };
    } catch (e) {
      return { ok: true, error: { type: "SQLError", text: String(e.message || e) } };
    } finally {
      db.close();
    }
  }
  const cell = (v) => (v === null ? "NULL" : String(v));
  function sameRows(got, exp, ordered) {
    if (!got || got.rows.length !== exp.rows.length) return false;
    const a = got.rows.map((r) => r.map(cell).join("\u0001"));
    const b = exp.rows.map((r) => r.map(cell).join("\u0001"));
    if ((got.rows[0] || []).length !== (exp.rows[0] || []).length) return false;
    if (!ordered) { a.sort(); b.sort(); }
    return a.every((x, i) => x === b[i]);
  }
  function tableEl(columns, rows) {
    const wrap = el("div", "sqltable");
    const t = el("table");
    const head = el("tr");
    (columns || []).forEach((c) => head.appendChild(el("th", "", c)));
    t.appendChild(head);
    rows.slice(0, 50).forEach((r) => {
      const tr = el("tr");
      r.forEach((v) => tr.appendChild(el("td", "", cell(v))));
      t.appendChild(tr);
    });
    wrap.appendChild(t);
    if (!rows.length) wrap.appendChild(el("p", "muted", T.no_rows || "0"));
    return wrap;
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
      ReferenceError: "Такой переменной или функции нет. Проверьте опечатки и объявлена ли переменная через let.",
      RangeError: "Значение вне допустимых границ — например, бесконечная рекурсия или неверная длина массива.",
      "JS:SyntaxError": "Ошибка в записи программы: проверьте круглые и фигурные скобки, кавычки и точки с запятой.",
      "JS:TypeError": "Действие с неподходящим значением: например, вызвали как функцию то, что функцией не является.",
      SQLError: "Ошибка в запросе: проверьте названия таблиц и столбцов, запятые и кавычки у текста.",
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
      ReferenceError: "Мұндай айнымалы немесе функция жоқ. Қате жазылмағанын және айнымалы let арқылы жарияланғанын тексеріңіз.",
      RangeError: "Мән рұқсат етілген шектен тыс — мысалы, шексіз рекурсия немесе массивтің қате ұзындығы.",
      "JS:SyntaxError": "Бағдарлама жазылуында қате бар: жай және фигуралы жақшаларды, тырнақшаларды және нүктелі үтірлерді тексеріңіз.",
      "JS:TypeError": "Сәйкес келмейтін мәнмен әрекет: мысалы, функция емес нәрсені функция ретінде шақырдыңыз.",
      SQLError: "Сұрауда қате бар: кестелер мен бағандардың атауларын, үтірлерді және мәтін тырнақшаларын тексеріңіз.",
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

  const hintFor = (type, kind) => {
    const h = ERROR_HINTS[LANG] || ERROR_HINTS.ru;
    return (kind === "js" && h["JS:" + type]) || h[type];
  };
  function showError(box, error, kind) {
    box.appendChild(el("pre", "out out--error", error.text));
    const hint = hintFor(error.type, kind);
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
    const pill = document.querySelector(`.steps a[data-step="${card.dataset.step}"]`);
    if (pill) pill.classList.add("is-done");
    const badge = card.querySelector(".task__badge");
    if (badge) badge.hidden = false;
    // все задания решены — открываем переход к следующему уроку
    const all = Array.from(document.querySelectorAll(".task"));
    const nextLink = document.querySelector(".js-next-lesson");
    if (nextLink && nextLink.hidden && all.every((c) => c.classList.contains("is-solved"))) {
      nextLink.hidden = false;
      document.querySelectorAll(".js-next-locked").forEach((e) => { e.hidden = true; });
      document.querySelectorAll(".js-next-done").forEach((e) => { e.hidden = false; });
    }
  }

  // ---------- Тесты и файлы Word / Excel / PowerPoint: проверяет сервер ----------
  async function postToServer(card, body, isForm) {
    try {
      const r = await fetch(card.dataset.submit, {
        method: "POST",
        headers: isForm ? { "X-CSRFToken": CSRF } : { "Content-Type": "application/json", "X-CSRFToken": CSRF },
        body: isForm ? body : JSON.stringify(body),
      });
      const data = await r.json().catch(() => ({ ok: false }));
      if (r.status === 403) data.error = T.locked_task || data.error;
      return data;
    } catch (e) {
      return { ok: false, error: T.save_error };
    }
  }

  function setupQuiz(card, out) {
    const btn = card.querySelector(".js-check");
    btn.addEventListener("click", async () => {
      const picked = card.querySelector("input[type=radio]:checked");
      if (!picked) { out.replaceChildren(el("p", "out--error", T.quiz_pick)); return; }
      btn.disabled = true;
      const r = await postToServer(card, { choice: Number(picked.value) });
      btn.disabled = false;
      card.querySelectorAll(".quiz__opt").forEach((o) => o.classList.remove("is-right", "is-wrong"));
      if (!r.ok) { out.replaceChildren(el("p", "out--error", r.error || T.save_error)); return; }
      const label = picked.closest(".quiz__opt");
      if (r.correct) {
        label.classList.add("is-right");
        out.replaceChildren(el("p", "out--ok", "🎉 " + T.quiz_right));
        markSolved(card);
      } else {
        label.classList.add("is-wrong");
        out.replaceChildren(el("p", "out--error", T.quiz_wrong));
      }
      if (!LOGGED_IN) out.appendChild(el("p", "muted", T.login_to_save));
    });
  }

  function setupFile(card, out) {
    const input = card.querySelector("input[type=file]");
    const name = card.querySelector(".upload__name");
    const btn = card.querySelector(".js-check");
    input.addEventListener("change", () => {
      name.textContent = input.files.length ? input.files[0].name : T.file_none;
      card.querySelector(".upload").classList.toggle("has-file", input.files.length > 0);
    });
    btn.addEventListener("click", async () => {
      if (!input.files.length) { out.replaceChildren(el("p", "out--error", T.file_pick)); return; }
      const form = new FormData();
      form.append("file", input.files[0]);
      btn.disabled = true;
      out.replaceChildren(el("p", "muted", T.file_checking));
      const r = await postToServer(card, form, true);
      btn.disabled = false;
      if (!r.ok) { out.replaceChildren(el("p", "out--error", r.error || T.save_error)); return; }
      const list = el("ol", "tests");
      r.results.forEach((x) => {
        const li = el("li", "test " + (x.ok ? "test--ok" : "test--fail"));
        li.appendChild(el("span", "test__title", (x.ok ? "✓ " : "✗ ") + x.msg));
        list.appendChild(li);
      });
      const summary = r.solved
        ? el("p", "out--ok", "🎉 " + T.file_all_passed)
        : el("p", "out--error", `${T.web_some_failed}: ${r.passed} / ${r.total}`);
      out.replaceChildren(summary, list);
      if (!LOGGED_IN) out.appendChild(el("p", "muted", T.login_to_save));
      if (r.solved || r.solved_ever) markSolved(card);
      out.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
  }

  // ---------- Задания ----------
  document.querySelectorAll(".task").forEach((card) => {
    if (card.dataset.kind === "quiz") return setupQuiz(card, card.querySelector(".task__out"));
    if (card.dataset.kind === "file") return setupFile(card, card.querySelector(".task__out"));
    const editor = card.querySelector("textarea.editor");
    const inputBox = card.querySelector("textarea.stdin");
    const out = card.querySelector(".task__out");
    const data = JSON.parse(card.querySelector("script.taskdata").textContent);
    const tests = data.tests;
    const starter = data.starter;
    const kind = card.dataset.kind;
    const textarea = editor;

    // Сообщение об ошибке под редактором
    const lintBox = el("div", "lint");
    lintBox.hidden = true;
    lintBox.setAttribute("role", "status");
    (card.querySelector(".stdin-box") || out).before(lintBox);

    // Редактор с подсветкой (CodeMirror); если библиотека не загрузилась — обычное поле
    let cm = null;
    if (window.CodeMirror) {
      cm = window.CodeMirror.fromTextArea(textarea, {
        mode: { web: "htmlmixed", js: "javascript", sql: "text/x-sqlite" }[kind] || "python", autoCloseTags: kind === "web", lineNumbers: true, indentUnit: 4, tabSize: 4, indentWithTabs: false,
        matchBrackets: true, autoCloseBrackets: true, viewportMargin: Infinity,
        extraKeys: {
          Tab: (c) => (c.somethingSelected() ? c.indentSelection("add") : c.replaceSelection("    ", "end")),
          "Shift-Tab": (c) => c.indentSelection("subtract"),
        },
      });
      cm.getInputField().setAttribute("aria-label", T.your_code || "code");
    } else {
      // Tab вставляет 4 пробела, Enter сохраняет отступ строки
      textarea.addEventListener("keydown", (e) => {
        if (e.key === "Tab") {
          e.preventDefault();
          textarea.setRangeText("    ", textarea.selectionStart, textarea.selectionEnd, "end");
        } else if (e.key === "Enter") {
          const before = textarea.value.slice(0, textarea.selectionStart);
          const line = before.split("\n").pop();
          let indent = line.match(/^\s*/)[0];
          if (/:\s*$/.test(line)) indent += "    ";
          e.preventDefault();
          textarea.setRangeText("\n" + indent, textarea.selectionStart, textarea.selectionEnd, "end");
        }
      });
    }
    const getCode = () => (cm ? cm.getValue() : textarea.value);
    const runner = kind === "js" ? runJS : runPython;
    const setCode = (v) => { if (cm) cm.setValue(v); else textarea.value = v; };

    // Отметка строки с ошибкой
    let marks = [], markedLine = null;
    function clearError() {
      marks.forEach((m) => m.clear());
      marks = [];
      if (cm && markedLine !== null) cm.removeLineClass(markedLine, "background", "cm-err-line");
      markedLine = null;
      lintBox.hidden = true;
    }
    function markError(err) {
      clearError();
      if (!err) return;
      const total = cm ? cm.lineCount() : getCode().split("\n").length;
      const ln = err.line ? Math.max(1, Math.min(err.line, total)) - 1 : null;
      if (cm && ln !== null) {
        cm.addLineClass(ln, "background", "cm-err-line");
        markedLine = ln;
        const len = cm.getLine(ln).length;
        const from = err.col ? Math.max(0, Math.min(err.col - 1, len - 1)) : 0;
        if (len) marks.push(cm.markText({ line: ln, ch: from }, { line: ln, ch: len }, { className: "cm-err-mark" }));
      }
      const hint = hintFor(err.type, kind);
      const where = ln === null ? "" : (LANG === "kk" ? `${ln + 1}-жол: ` : `Строка ${ln + 1}: `);
      lintBox.replaceChildren(el("strong", "", "⚠ " + where), document.createTextNode(hint || err.msg || err.type));
      if (err.msg && hint) lintBox.appendChild(el("span", "lint__py", " (" + err.msg + ")"));
      lintBox.hidden = false;
    }

    // Проверка записи через небольшую паузу после набора
    let lintTimer = null, lintSeq = 0;
    const scheduleLint = () => {
      clearTimeout(lintTimer);
      lintTimer = setTimeout(async () => {
        const my = ++lintSeq;
        const res = kind === "js" ? lintJS(getCode()) : await lintCode(getCode());
        if (my === lintSeq && res !== undefined) markError(res);
      }, 700);
    };
    if (kind === "tested" || kind === "project" || kind === "js") {
      if (cm) cm.on("change", scheduleLint);
      else textarea.addEventListener("input", scheduleLint);
    }

    // HTML/CSS: живой предпросмотр страницы
    const frame = card.querySelector("iframe.preview");
    const renderPage = (code) => new Promise((resolve) => {
      if (!frame) return resolve(null);
      frame.onload = () => resolve(frame.contentDocument);
      frame.srcdoc = code;
    });
    if (kind === "web" && frame) {
      let t = null;
      const live = () => { clearTimeout(t); t = setTimeout(() => renderPage(getCode()), 300); };
      if (cm) cm.on("change", live); else textarea.addEventListener("input", live);
      renderPage(getCode());
    }

    async function runSqlTask() {
      out.replaceChildren(el("p", "muted", T.running));
      const res = await runSQL((tests[0] || {}).setup, getCode(), (tests[0] || {}).after);
      out.replaceChildren(el("p", "out__label", T.sql_result || T.output));
      if (!res.ok) return showFatal(out, res);
      if (res.error) { showError(out, res.error, kind); return; }
      out.appendChild(tableEl(res.columns, res.rows));
    }

    async function checkSql() {
      const code = getCode();
      out.replaceChildren(el("p", "muted", T.checking));
      let passed = 0, shownFail = false;
      const list = el("ol", "tests");
      for (let i = 0; i < tests.length; i++) {
        const t = tests[i];
        const res = await runSQL(t.setup, code, t.after);
        const ok = res.ok && !res.error && sameRows(res, t.expected, t.ordered);
        passed += ok;
        const li = el("li", "test " + (ok ? "test--ok" : "test--fail"));
        li.appendChild(el("span", "test__title", `${T.test} ${i + 1}: ${ok ? "✓ " + T.passed : "✗ " + T.failed}`));
        if (!ok && !shownFail) {
          shownFail = true;
          li.appendChild(el("span", "test__label", T.expected));
          li.appendChild(tableEl(t.expected.columns, t.expected.rows));
          li.appendChild(el("span", "test__label", T.got));
          if (!res.ok) showFatal(li, res);
          else if (res.error) showError(li, res.error, kind);
          else li.appendChild(tableEl(res.columns, res.rows));
        }
        list.appendChild(li);
      }
      const summary = passed === tests.length
        ? el("p", "out--ok", "🎉 " + T.all_passed)
        : el("p", "out--error", `${T.some_failed}: ${passed} / ${tests.length}`);
      out.replaceChildren(summary, list);
      const r = await save(card, code, passed);
      if (!LOGGED_IN) out.appendChild(el("p", "muted", T.login_to_save));
      else if (!r || !r.ok) out.appendChild(el("p", "out--error", T.save_error));
      if (passed === tests.length || (r && r.solved)) markSolved(card);
      out.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    async function checkWeb() {
      const code = getCode();
      const doc = await renderPage(code);
      const checks = tests;
      const res = doc ? window.runWebChecks(doc, frame.contentWindow, checks) : checks.map(() => false);
      const passed = res.filter(Boolean).length;
      const list = el("ol", "tests");
      res.forEach((ok, i) => {
        const c = checks[i];
        const msg = Array.isArray(c.msg) ? (LANG === "kk" && c.msg[1] ? c.msg[1] : c.msg[0]) : (c.msg || c.sel);
        const li = el("li", "test " + (ok ? "test--ok" : "test--fail"));
        li.appendChild(el("span", "test__title", (ok ? "✓ " : "✗ ") + msg));
        list.appendChild(li);
      });
      const summary = passed === checks.length
        ? el("p", "out--ok", "🎉 " + T.web_all_passed)
        : el("p", "out--error", `${T.web_some_failed}: ${passed} / ${checks.length}`);
      out.replaceChildren(summary, list);
      const r = await save(card, code, passed);
      if (!LOGGED_IN) out.appendChild(el("p", "muted", T.login_to_save));
      else if (!r || !r.ok) out.appendChild(el("p", "out--error", T.save_error));
      if (passed === checks.length || (r && r.solved)) markSolved(card);
      out.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    card.querySelector(".js-reset")?.addEventListener("click", () => {
      if (confirm(T.reset_confirm)) { setCode(starter); clearError(); if (kind === "web") renderPage(starter); }
    });

    // ▶ Запустить
    card.querySelector(".js-run")?.addEventListener("click", async () => {
      out.replaceChildren(el("p", "muted", (worker || kind === "js") ? T.running : T.loading_python));
      if (kind === "sql") return runSqlTask();
      const res = await runner(getCode(), splitInput(inputBox.value), true);
      out.replaceChildren(el("p", "out__label", T.output));
      if (!res.ok) return showFatal(out, res);
      out.appendChild(el("pre", "out", res.stdout || T.no_output));
      if (res.error) { showError(out, res.error, kind); markError(res.error); } else clearError();
      card.dataset.ranOk = res.error ? "" : "1";
    });

    // ✓ Проверить / Сдать проект
    card.querySelector(".js-check").addEventListener("click", async () => {
      if (kind === "web") return checkWeb();
      if (kind === "sql") return checkSql();
      const code = getCode();
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

      out.replaceChildren(el("p", "muted", (worker || kind === "js") ? T.checking : T.loading_python));
      let passed = 0, shownFail = false;
      const results = el("ol", "tests");
      for (let i = 0; i < tests.length; i++) {
        const t = tests[i];
        const res = await runner(code, splitInput(t.input), false);
        const li = el("li", "test");
        const ok = res.ok && !res.error && normalize(res.stdout) === normalize(t.output);
        passed += ok;
        li.classList.add(ok ? "test--ok" : "test--fail");
        li.appendChild(el("span", "test__title", `${T.test} ${i + 1}: ${ok ? "✓ " + T.passed : "✗ " + T.failed}`));
        if (!ok && !shownFail) {
          shownFail = true;  // подробности только по первому непройденному тесту
          if (t.input) { li.appendChild(el("span", "test__label", T.given_input)); li.appendChild(el("pre", "out", t.input)); }
          li.appendChild(el("span", "test__label", T.expected)); li.appendChild(el("pre", "out", t.output));
          li.appendChild(el("span", "test__label", T.got));
          if (!res.ok) showFatal(li, res);
          else {
            li.appendChild(el("pre", "out", res.stdout || T.no_output));
            if (res.error) { showError(li, res.error, kind); markError(res.error); }
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
      if (passed === tests.length || (r && r.solved)) { markSolved(card); clearError(); }
      out.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
  });

  // Заранее загружаем Python, пока ученик читает теорию
  if (document.querySelector('.task[data-kind="tested"], .task[data-kind="project"]')) {
    setTimeout(() => { if (!worker) startWorker(); }, 1500);
  }
})();
