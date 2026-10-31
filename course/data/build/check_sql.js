// Проверка курса SQL на том же движке, что и на сайте (sql.js):
// эталон каждого задания даёт ожидаемый ответ на всех наборах данных.
//   node course/data/build/check_sql.js
const fs = require("fs");
const path = require("path");
const root = path.resolve(__dirname, "../../..");
const initSqlJs = require(path.join(root, "static/vendor/sqljs/sql-wasm.js"));
const data = JSON.parse(fs.readFileSync(path.join(root, "course/data/sql.json"), "utf8"));
const cell = (v) => (v === null ? "NULL" : String(v));
const key = (rows, ordered) => { const a = rows.map((r) => r.map(cell).join("\u0001")); if (!ordered) a.sort(); return JSON.stringify(a); };

initSqlJs({ locateFile: (f) => path.join(root, "static/vendor/sqljs", f) }).then((SQL) => {
  let errors = 0, total = 0;
  for (const m of data.modules) for (const l of m.lessons) for (const [i, t] of l.tasks.entries()) {
    total++;
    for (const test of t.tests) {
      const db = new SQL.Database();
      db.run(test.setup);
      let res;
      if (test.after) { db.run(t.solution); res = db.exec(test.after); } else res = db.exec(t.solution);
      const last = res[res.length - 1] || { values: [] };
      if (key(last.values, test.ordered) !== key(test.expected.rows, test.ordered)) {
        errors++;
        console.log(`урок ${l.number} задание ${i + 1}: sql.js даёт другой ответ`, JSON.stringify(last.values), JSON.stringify(test.expected.rows));
      }
      db.close();
    }
  }
  console.log(errors ? `Ошибок: ${errors}` : `OK: заданий ${total}, sql.js совпадает с ожидаемыми ответами`);
  process.exit(errors ? 1 : 0);
});
