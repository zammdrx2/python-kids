/*
 * Запуск JavaScript ученика: console.log собирается в текст, input() читает входные данные.
 * Используется в Web Worker на сайте и в Node при сборке курса (ожидаемый вывод тестов).
 */
(function (root) {
  function fmt(v, inner) {
    if (typeof v === "string") return inner ? JSON.stringify(v) : v;
    if (Array.isArray(v)) return "[" + v.map((x) => fmt(x, true)).join(", ") + "]";
    if (v && typeof v === "object") {
      return "{" + Object.keys(v).map((k) => k + ": " + fmt(v[k], true)).join(", ") + "}";
    }
    return String(v);
  }

  function runJS(code, inputs, showPrompt) {
    const out = [];
    const log = (...args) => { out.push(args.map((a) => fmt(a, false)).join(" ")); };
    const lines = Array.from(inputs || []);
    let pos = 0;
    const input = (prompt) => {
      if (pos >= lines.length) throw new Error("input(): входные данные закончились");
      const value = lines[pos++];
      if (showPrompt && prompt !== undefined) out.push(String(prompt) + value);
      return value;
    };
    const consoleObj = { log, info: log, warn: log, error: log };
    let error = null;
    try {
      const fn = new Function("console", "input", "prompt", "alert", code);
      fn(consoleObj, input, input, log);
    } catch (e) {
      const name = (e && e.name) || "Error";
      let line = null;
      const m = String((e && e.stack) || "").match(/<anonymous>:(\d+):\d+/);
      if (m) line = Math.max(1, Number(m[1]) - 2);  // new Function добавляет две строки в начале
      error = { type: name, text: name + ": " + ((e && e.message) || e), line };
    }
    return { stdout: out.length ? out.join("\n") + "\n" : "", error };
  }

  root.runJS = runJS;
  if (typeof module !== "undefined") module.exports = runJS;
})(typeof self !== "undefined" ? self : globalThis);
