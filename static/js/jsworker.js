/* Web Worker для JavaScript ученика: бесконечный цикл не повесит страницу — её остановят по таймауту. */
importScripts("jsrunner.js");
self.onmessage = (e) => {
  const { id, code, inputs, showPrompt } = e.data;
  const res = self.runJS(code, inputs, showPrompt);
  self.postMessage({ id, ok: true, stdout: res.stdout, error: res.error });
};
