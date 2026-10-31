// Проверка курса HTML/CSS в настоящем браузере:
// эталон каждого задания проходит все проверки, а начальный код — нет.
//   node course/data/build/check_web.js
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "../../..");
const data = JSON.parse(fs.readFileSync(path.join(root, "course/data/web.json"), "utf8"));
const checksJs = fs.readFileSync(path.join(root, "static/js/webchecks.js"), "utf8");

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.route("**/*", (r) => (r.request().url().startsWith("http") ? r.abort() : r.continue()));
  const run = async (html, tests) => {
    await page.setContent(html || "<p></p>", { waitUntil: "domcontentloaded" });
    await page.addScriptTag({ content: checksJs });
    return page.evaluate((t) => window.runWebChecks(document, window, t), tests);
  };
  let errors = 0, total = 0;
  for (const m of data.modules) {
    for (const l of m.lessons) {
      for (const [i, t] of l.tasks.entries()) {
        total++;
        const sol = await run(t.solution, t.tests);
        sol.forEach((ok, k) => { if (!ok) { errors++; console.log(`урок ${l.number} задание ${i + 1}: эталон не прошёл «${t.tests[k].msg[0]}»`); } });
        const st = await run(t.starter, t.tests);
        if (st.every(Boolean)) { errors++; console.log(`урок ${l.number} задание ${i + 1}: начальный код уже проходит все проверки`); }
      }
    }
  }
  await browser.close();
  console.log(errors ? `Ошибок: ${errors}` : `OK: заданий ${total}, все эталоны проходят, начальный код — нет`);
  process.exit(errors ? 1 : 0);
})();
