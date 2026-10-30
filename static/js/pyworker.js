/*
 * Web Worker: выполняет код ученика в Pyodide, не блокируя страницу.
 * Если программа зависла (бесконечный цикл), основная страница просто
 * останавливает этот Worker и создаёт новый.
 */
let pyodideReady = null;

const RUNNER = `
import sys, io, json, traceback

def __run(code, inputs, show_prompt):
    out = io.StringIO()
    lines = list(inputs)
    pos = [0]

    def _input(prompt=""):
        if show_prompt:
            out.write(str(prompt))
        if pos[0] >= len(lines):
            raise EOFError("input(): входные данные закончились")
        value = lines[pos[0]]
        pos[0] += 1
        if show_prompt:
            out.write(value + "\\n")
        return value

    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = out
    error = None
    try:
        exec(compile(code, "<код>", "exec"), {"__name__": "__main__", "input": _input})
    except SystemExit:
        pass
    except BaseException as e:
        frames = [f for f in traceback.extract_tb(e.__traceback__) if f.filename == "<код>"]
        text = ""
        if frames:
            text = "Traceback (most recent call last):\\n" + "".join(traceback.format_list(frames))
        text += "".join(traceback.format_exception_only(type(e), e))
        error = {"type": type(e).__name__, "text": text}
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return json.dumps({"stdout": out.getvalue(), "error": error})
`;

self.onmessage = async (event) => {
  const { id, type, indexURL, code, inputs, showPrompt } = event.data;
  try {
    if (!pyodideReady) {
      importScripts(indexURL + "pyodide.js");
      pyodideReady = loadPyodide({ indexURL }).then((py) => {
        py.runPython(RUNNER);
        return py;
      });
    }
    const py = await pyodideReady;
    if (type === "init") {
      self.postMessage({ id, ok: true });
      return;
    }
    const run = py.globals.get("__run");
    const result = run(code, py.toPy(inputs || []), Boolean(showPrompt));
    run.destroy();
    self.postMessage({ id, ok: true, ...JSON.parse(result) });
  } catch (err) {
    self.postMessage({ id, ok: false, fatal: String(err) });
  }
};
