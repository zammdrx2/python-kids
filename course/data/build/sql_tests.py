"""
Итоговые тесты модулей курса SQL: по 20 вопросов на модуль.

Запуск:  python course/data/build/sql_tests.py
Запросы выполняются на том же движке, что и на сайте (sql.js), на маленьких
таблицах, которые показаны над запросом. Результат должен совпасть с правильным вариантом:
одно значение - как есть, несколько - через запятую, строки результата - каждая с новой строки.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tests_common import Q, build, node_run  # noqa: E402

TABLES = {
    "students": (["id", "name", "age", "city"], [
        (1, "Айжан", 12, "Актобе"), (2, "Дамир", 13, "Астана"), (3, "Алия", 12, "Актобе"),
        (4, "Ерлан", 14, "Алматы"), (5, "Дана", 13, "Актобе")]),
    "scores": (["student_id", "subject", "score"], [
        (1, "Математика", 5), (1, "История", 4), (2, "Математика", 4),
        (3, "Математика", 3), (3, "История", 5), (5, "История", 4)]),
    "products": (["id", "name", "price", "stock"], [
        (1, "Ручка", 150, 40), (2, "Тетрадь", 300, 25), (3, "Рюкзак", 9000, 3), (4, "Пенал", 1200, 0)]),
    "orders": (["id", "product_id", "qty"], [(1, 1, 5), (2, 2, 3), (3, 1, 2), (4, 3, 1)]),
    "pets": (["id", "name", "kind", "age"], [
        (1, "Барсик", "кот", 3), (2, "Шарик", "собака", 5), (3, "Кеша", "попугай", None), (4, "Мурка", "кот", 2)]),
}


def cell(v):
    return "NULL" if v is None else str(v)


def show(name):
    cols, rows = TABLES[name]
    grid = [cols] + [[cell(v) for v in r] for r in rows]
    w = [max(len(row[i]) for row in grid) for i in range(len(cols))]
    lines = [" | ".join(c.ljust(w[i]) for i, c in enumerate(row)).rstrip() for row in grid]
    return "\n".join([f"-- {name}"] + ["-- " + l for l in lines])


def setup(name):
    cols, rows = TABLES[name]
    vals = ", ".join("(" + ", ".join("NULL" if v is None else (str(v) if isinstance(v, int) else f"'{v}'") for v in r) + ")"
                     for r in rows)
    return f"CREATE TABLE {name} ({', '.join(cols)});\nINSERT INTO {name} VALUES {vals};"


def S(ru, kk, options, answer, query, tables, **kw):
    """Вопрос с запросом: над ним показаны таблицы, при сборке запрос выполняется."""
    tables = tables.split()
    code = "\n\n".join([show(t) for t in tables] + [query])
    run_code = "\n".join(setup(t) for t in ("students", "scores", "products", "orders", "pets")) + "\n" + query
    return Q(ru, kk, options, answer, code=code, exec_code=run_code, **kw)


R = ("Что вернёт запрос?", "Сұрау не қайтарады?")
ERR = ("ошибка", "қате")

NODE = r"""
const fs = require("fs"), path = require("path");
const [src, root] = process.argv.slice(-2);
const initSqlJs = require(path.join(root, "static/vendor/sqljs/sql-wasm.js"));
const codes = JSON.parse(fs.readFileSync(src, "utf8"));
const cell = (v) => (v === null ? "NULL" : String(v));
initSqlJs({ locateFile: (f) => path.join(root, "static/vendor/sqljs", f) }).then((SQL) => {
  const res = codes.map((c) => {
    const db = new SQL.Database();
    try {
      const r = db.exec(c);
      const last = r[r.length - 1] || { values: [] };
      const rows = last.values.map((row) => row.map(cell).join(" | "));
      return { out: last.values.every((row) => row.length === 1) ? rows.join(", ") : rows.join("\n") };
    } catch (e) { return { error: String(e.message || e) }; } finally { db.close(); }
  });
  process.stdout.write(JSON.stringify(res));
});
"""


def runner(codes):
    return node_run(NODE, codes)


M1 = [
    Q("Что такое таблица в базе данных?", "Деректер базасындағы кесте деген не?",
      [("Строки и столбцы с данными, как в Excel", "Excel сияқты деректері бар жолдар мен бағандар"),
       ("Программа на Python", "Python бағдарламасы"), ("Картинка", "Сурет"), ("Веб-страница", "Веб-бет")], 0),
    Q("Что значит * в SELECT * FROM students?", "SELECT * FROM students ішіндегі * нені білдіреді?",
      [("Все столбцы", "Барлық бағандар"), ("Умножение", "Көбейту"), ("Первую строку", "Бірінші жол"),
       ("Все таблицы", "Барлық кестелер")], 0),
    Q("Что пишут после FROM?", "FROM-нан кейін не жазады?",
      [("Имя таблицы", "Кестенің аты"), ("Условие", "Шарт"), ("Имя столбца", "Бағанның аты"), ("Число строк", "Жолдар саны")], 0),
    S(*R, ["Айжан, Алия, Дана", "Дамир, Ерлан", "Айжан, Алия", "Актобе"], 0,
      "SELECT name FROM students WHERE city = 'Актобе';", "students"),
    S(*R, ["Ерлан", "Дамир, Ерлан, Дана", "Дамир, Дана", "Ерлан, Дана"], 1,
      "SELECT name FROM students WHERE age > 12;", "students"),
    S(*R, ["Айжан, Алия", "Айжан, Дамир, Алия, Дана", "Ерлан", "Дамир, Дана"], 1,
      "SELECT name FROM students WHERE age <= 13;", "students"),
    S(*R, ["Дана", "Айжан, Алия, Дана", "Дамир, Дана", "Айжан, Дана"], 0,
      "SELECT name FROM students WHERE city = 'Актобе' AND age = 13;", "students"),
    S(*R, ["Дамир, Ерлан", "Дамир", "Ерлан", "Айжан, Алия"], 0,
      "SELECT name FROM students WHERE city = 'Астана' OR city = 'Алматы';", "students"),
    S(*R, ["Айжан, Алия", "Алия", "Айжан, Алия, Дана", "Дана"], 0,
      "SELECT name FROM students WHERE name LIKE 'А%';", "students"),
    S(*R, ["Дана", "Айжан, Алия", "Алия, Дана", "Дамир, Дана"], 0,
      "SELECT name FROM students WHERE name LIKE '%а';", "students"),
    Q("Что значит % в LIKE 'А%'?", "LIKE 'А%' ішіндегі % нені білдіреді?",
      [("Любое количество любых символов", "Кез келген таңбалардың кез келген саны"), ("Ровно один символ", "Дәл бір таңба"),
       ("Процент", "Пайыз"), ("Цифру", "Цифр")], 0),
    S(*R, ["Айжан | 12", "Айжан, 12", "1 | Айжан | 12 | Актобе", "Айжан"], 0,
      "SELECT name, age FROM students WHERE id = 1;", "students"),
    Q("Какой знак значит «не равно» в SQL?", "SQL-де қай таңба «тең емес» дегенді білдіреді?", ["<>", "=!", "!==", "=/="], 0),
    S(*R, ["Дамир, Ерлан", "Айжан, Алия, Дана", "Ерлан", "Дамир"], 0,
      "SELECT name FROM students WHERE city <> 'Актобе';", "students"),
    Q("В чём ошибка запроса?", "Сұраудың қатесі неде?",
      [("Текст надо брать в кавычки: 'Актобе'", "Мәтінді тырнақшаға алу керек: 'Актобе'"),
       ("Нельзя писать WHERE", "WHERE жазуға болмайды"), ("Нужно SELECT *", "SELECT * керек"),
       ("Ошибки нет", "Қате жоқ")], 0, "SELECT name FROM students WHERE city = Актобе;", run=False),
    Q("Чем заканчивают SQL-запрос?", "SQL-сұрау немен аяқталады?", [";", ".", ":", "!"], 0),
    S(*R, ["Математика, История", "Математика, Математика, Математика", "5, 4, 3", "4, 3"], 1,
      "SELECT subject FROM scores WHERE subject = 'Математика';", "scores"),
    S(*R, ["5, 5", "5", "4, 5", "Математика, История"], 0,
      "SELECT score FROM scores WHERE score = 5;", "scores"),
    S(*R, ["0", ("пустой результат", "бос нәтиже"), "NULL", ERR], 1,
      "SELECT name FROM students WHERE age > 20;", "students", out=""),
    S(*R, ["Алия", "Айжан, Алия", "Алия, Дана", "Айжан"], 0,
      "SELECT name FROM students WHERE name LIKE '_л%';", "students"),
]

M2 = [
    S(*R, ["Ерлан, Дамир, Дана, Айжан, Алия", "Айжан, Алия, Дамир, Дана, Ерлан", "Ерлан", "Айжан, Дамир, Алия, Ерлан, Дана"], 0,
      "SELECT name FROM students ORDER BY age DESC, id;", "students"),
    S(*R, ["Айжан, Алия, Дамир", "Айжан, Алия, Дана, Дамир, Ерлан", "Алия, Айжан", "Айжан, Алия"], 3,
      "SELECT name FROM students ORDER BY name LIMIT 2;", "students"),
    Q("Что делает DESC?", "DESC не істейді?",
      [("Сортирует по убыванию", "Кему ретімен сұрыптайды"), ("Сортирует по возрастанию", "Өсу ретімен сұрыптайды"),
       ("Удаляет строки", "Жолдарды өшіреді"), ("Считает строки", "Жолдарды санайды")], 0),
    S(*R, ["5", "4", "3", "13"], 0, "SELECT COUNT(*) FROM students;", "students"),
    S(*R, ["3", "2", "5", "Актобе"], 0, "SELECT COUNT(*) FROM students WHERE city = 'Актобе';", "students"),
    S(*R, ["14", "12", "13", "64"], 0, "SELECT MAX(age) FROM students;", "students"),
    S(*R, ["12", "14", "13", "12.8"], 3, "SELECT AVG(age) FROM students;", "students"),
    S(*R, ["64", "5", "14", "12.8"], 0, "SELECT SUM(age) FROM students;", "students"),
    S(*R, ["3", "5", "2", "1"], 0, "SELECT COUNT(DISTINCT city) FROM students;", "students"),
    S(*R, ["Актобе, Астана, Алматы", "Актобе, Астана, Актобе, Алматы, Актобе", "Актобе", "3"], 0,
      "SELECT DISTINCT city FROM students;", "students"),
    Q("Что делает AS в SELECT age AS возраст?", "SELECT age AS возраст ішіндегі AS не істейді?",
      [("Даёт столбцу результата новое имя", "Нәтиже бағанына жаңа ат береді"), ("Меняет таблицу", "Кестені өзгертеді"),
       ("Фильтрует строки", "Жолдарды сүзеді"), ("Сортирует", "Сұрыптайды")], 0),
    S(*R, ["9000", "150", "300", "10650"], 0, "SELECT MAX(price) FROM products;", "products"),
    S(*R, ["Рюкзак", "Ручка", "Пенал", "Тетрадь"], 1, "SELECT name FROM products ORDER BY price LIMIT 1;", "products"),
    S(*R, ["68", "4", "40", "17"], 0, "SELECT SUM(stock) FROM products;", "products"),
    S(*R, ["3", "4", "1", "0"], 0, "SELECT COUNT(*) FROM products WHERE stock > 0;", "products"),
    S(*R, ["3", "5", "12", "4.2"], 3, "SELECT ROUND(AVG(score), 1) FROM scores;", "scores"),
    S(*R, ["Рюкзак | 9000", "Рюкзак", "9000", "Пенал | 1200"], 0,
      "SELECT name, price FROM products ORDER BY price DESC LIMIT 1;", "products"),
    Q("Где в запросе пишут ORDER BY?", "Сұрауда ORDER BY қай жерге жазылады?",
      [("После WHERE, перед LIMIT", "WHERE-ден кейін, LIMIT-тен бұрын"), ("Сразу после SELECT", "SELECT-тен кейін бірден"),
       ("Перед FROM", "FROM-нан бұрын"), ("В самом начале", "Ең басында")], 0),
    S(*R, ["3", "12", "5", "4"], 0, "SELECT MIN(score) FROM scores;", "scores"),
    S(*R, ["2", "3", "1", "0"], 0, "SELECT COUNT(*) FROM students WHERE age = 13;", "students"),
]

M3 = [
    S(*R, ["Актобе | 3\nАлматы | 1\nАстана | 1", "Актобе | 3", "3, 1, 1", "Актобе, Алматы, Астана"], 0,
      "SELECT city, COUNT(*) FROM students GROUP BY city ORDER BY city;", "students"),
    Q("Что делает GROUP BY?", "GROUP BY не істейді?",
      [("Собирает строки с одинаковым значением в группы", "Мәні бірдей жолдарды топтарға жинайды"),
       ("Сортирует", "Сұрыптайды"), ("Соединяет таблицы", "Кестелерді біріктіреді"), ("Удаляет повторы в таблице", "Кестедегі қайталауларды өшіреді")], 0),
    S(*R, ["История | 13\nМатематика | 12", "История | 4.33\nМатематика | 4", "13, 12", "История, Математика"], 0,
      "SELECT subject, SUM(score) FROM scores GROUP BY subject ORDER BY subject;", "scores"),
    S(*R, ["Актобе", "Актобе, Алматы, Астана", "Алматы, Астана", "3"], 0,
      "SELECT city FROM students GROUP BY city HAVING COUNT(*) > 1;", "students"),
    Q("Чем HAVING отличается от WHERE?", "HAVING пен WHERE айырмашылығы неде?",
      [("HAVING фильтрует группы после GROUP BY", "HAVING GROUP BY-дан кейін топтарды сүзеді"),
       ("Ничем", "Ешнәрсемен"), ("HAVING сортирует", "HAVING сұрыптайды"), ("WHERE работает только с числами", "WHERE тек сандармен жұмыс істейді")], 0),
    S(*R, ["1, 3", "1, 2, 3", "3", "1, 3, 5"], 0,
      "SELECT student_id FROM scores GROUP BY student_id HAVING COUNT(*) = 2;", "scores"),
    S(*R, ["Айжан | 5", "Айжан | 5\nАйжан | 4", "1 | 5", "Айжан"], 1,
      "SELECT students.name, scores.score\nFROM scores JOIN students ON scores.student_id = students.id\nWHERE students.id = 1;", "students scores"),
    Q("Зачем нужен JOIN?", "JOIN не үшін керек?",
      [("Соединить строки двух таблиц по общему столбцу", "Екі кестенің жолдарын ортақ баған арқылы біріктіру"),
       ("Удалить таблицу", "Кестені өшіру"), ("Посчитать строки", "Жолдарды санау"), ("Отсортировать", "Сұрыптау")], 0),
    Q("Что пишут после ON в JOIN?", "JOIN-дағы ON-нан кейін не жазады?",
      [("Условие, по которому совпадают строки", "Жолдар сәйкес келетін шарт"), ("Имя новой таблицы", "Жаңа кестенің аты"),
       ("Количество строк", "Жолдар саны"), ("Порядок сортировки", "Сұрыптау реті")], 0),
    S(*R, ["Дана", "Дамир", "Айжан", "Алия"], 0,
      "SELECT students.name FROM scores\nJOIN students ON scores.student_id = students.id\nWHERE scores.subject = 'История' AND scores.score = 4 AND students.age = 13;", "students scores"),
    S(*R, ["6", "5", "4", "30"], 0,
      "SELECT COUNT(*) FROM scores JOIN students ON scores.student_id = students.id;", "students scores"),
    S(*R, ["Айжан | 2\nАлия | 2\nДамир | 1\nДана | 1", "Айжан | 2", "2, 2, 1, 1", "4"], 0,
      "SELECT students.name, COUNT(*) FROM scores\nJOIN students ON scores.student_id = students.id\nGROUP BY students.id ORDER BY COUNT(*) DESC, students.name;", "students scores"),
    S(*R, ["Актобе | 12.33\nАлматы | 14\nАстана | 13", "Актобе | 12.67\nАлматы | 14\nАстана | 13", "12.33, 14, 13", "Актобе | 37"], 0,
      "SELECT city, ROUND(AVG(age), 2) FROM students GROUP BY city ORDER BY city;", "students"),
    S(*R, ["Ручка | 7\nТетрадь | 3\nРюкзак | 1", "Ручка | 5\nТетрадь | 3\nРюкзак | 1", "11", "Ручка | 7"], 0,
      "SELECT products.name, SUM(orders.qty) FROM orders\nJOIN products ON orders.product_id = products.id\nGROUP BY products.id ORDER BY products.id;", "products orders"),
    Q("Какой порядок частей запроса правильный?", "Сұрау бөліктерінің қай реті дұрыс?",
      ["SELECT … FROM … WHERE … GROUP BY … HAVING … ORDER BY …", "SELECT … WHERE … FROM … ORDER BY … GROUP BY …",
       "FROM … SELECT … HAVING … WHERE …", "SELECT … GROUP BY … FROM … WHERE …"], 0),
    S(*R, ["2", "3", "1", "5"], 0, "SELECT COUNT(*) FROM (SELECT city FROM students GROUP BY city HAVING COUNT(*) = 1);", "students"),
    S(*R, ["История | 5\nМатематика | 5", "История | 4\nМатематика | 3", "5", "История | 13"], 0,
      "SELECT subject, MAX(score) FROM scores GROUP BY subject ORDER BY subject;", "scores"),
    Q("Почему students.name пишут через точку?", "students.name неге нүкте арқылы жазылады?",
      [("Чтобы указать, из какой таблицы столбец", "Баған қай кестеден екенін көрсету үшін"), ("Это дробное число", "Бұл бөлшек сан"),
       ("Так сортируют", "Осылай сұрыптайды"), ("Это комментарий", "Бұл түсініктеме")], 0),
    S(*R, ["2", "3", "1", "4"], 0, "SELECT COUNT(DISTINCT subject) FROM scores;", "scores"),
    S(*R, ["Математика", "История", "Математика, История", "12"], 0,
      "SELECT subject FROM scores GROUP BY subject HAVING SUM(score) = 12;", "scores"),
]

M4 = [
    S(*R, ["6", "5", "1", ERR], 0,
      "INSERT INTO students VALUES (6, 'Тимур', 11, 'Астана');\nSELECT COUNT(*) FROM students;", "students"),
    Q("Какой запрос добавляет строку?", "Қай сұрау жол қосады?",
      ["INSERT INTO", "UPDATE", "DELETE FROM", "SELECT"], 0),
    Q("Какой запрос меняет данные в уже существующих строках?", "Қай сұрау бар жолдардағы деректерді өзгертеді?",
      ["UPDATE … SET …", "INSERT INTO …", "CREATE TABLE …", "DROP TABLE …"], 0),
    S(*R, ["13", "12", "14", "1"], 0, "UPDATE students SET age = 13 WHERE id = 1;\nSELECT age FROM students WHERE id = 1;", "students"),
    S(*R, ["4", "5", "0", "1"], 0, "DELETE FROM students WHERE id = 4;\nSELECT COUNT(*) FROM students;", "students"),
    Q("Что сделает DELETE FROM students; без WHERE?", "WHERE жоқ DELETE FROM students; не істейді?",
      [("Удалит все строки таблицы", "Кестенің барлық жолын өшіреді"), ("Ничего", "Ештеңе"),
       ("Удалит первую строку", "Бірінші жолды өшіреді"), ("Выдаст ошибку", "Қате береді")], 0),
    S(*R, ["2", "3", "0", "5"], 0, "DELETE FROM students WHERE city = 'Актобе';\nSELECT COUNT(*) FROM students;", "students"),
    S(*R, ["Айжан, Алия, Дана", "Дамир, Ерлан", "Айжан, Дамир, Алия, Ерлан, Дана", ("пусто", "бос")], 2,
      "UPDATE students SET city = 'Актобе';\nSELECT name FROM students WHERE city = 'Актобе';", "students"),
    S(*R, ["170", "150", "300", "320"], 0, "UPDATE products SET price = price + 20 WHERE id = 1;\nSELECT price FROM products WHERE id = 1;", "products"),
    S(*R, ["Тимур | 11", "Тимур", "6", ERR], 0,
      "INSERT INTO students (id, name, age) VALUES (6, 'Тимур', 11);\nSELECT name, age FROM students WHERE id = 6;", "students"),
    S(*R, ["NULL", "Астана", ("пусто", "бос"), ERR], 0,
      "INSERT INTO students (id, name, age) VALUES (6, 'Тимур', 11);\nSELECT city FROM students WHERE id = 6;", "students"),
    Q("Как поменять два столбца сразу?", "Екі бағанды бірден қалай өзгертеді?",
      ["UPDATE students SET age = 13, city = 'Астана' WHERE id = 1;", "UPDATE students SET age = 13 AND city = 'Астана';",
       "UPDATE students age = 13, city = 'Астана';", "SET students age = 13 WHERE id = 1;"], 0),
    S(*R, ["2", "3", "4", "0"], 0, "DELETE FROM products WHERE price > 1000;\nSELECT COUNT(*) FROM products;", "products"),
    S(*R, ["45", "40", "5", "35"], 0, "UPDATE products SET stock = stock + 5 WHERE name = 'Ручка';\nSELECT stock FROM products WHERE name = 'Ручка';", "products"),
    Q("Какой запрос создаёт новую таблицу?", "Қай сұрау жаңа кесте жасайды?",
      ["CREATE TABLE", "INSERT INTO", "NEW TABLE", "MAKE TABLE"], 0),
    S(*R, ["Книга | 2", "Книга", "2", ERR], 0,
      "CREATE TABLE books (title TEXT, copies INTEGER);\nINSERT INTO books VALUES ('Книга', 2);\nSELECT * FROM books;", ""),
    Q("Почему UPDATE почти всегда пишут с WHERE?", "UPDATE неге көбіне WHERE-мен жазылады?",
      [("Иначе изменятся все строки", "Әйтпесе барлық жол өзгереді"), ("Без WHERE он не работает", "WHERE-сіз ол жұмыс істемейді"),
       ("Так быстрее", "Осылай жылдамырақ"), ("Это правило оформления", "Бұл безендіру ережесі")], 0),
    S(*R, ["2", "3", "4", "6"], 0, "DELETE FROM scores WHERE score <= 4;\nSELECT COUNT(*) FROM scores;", "scores"),
    S(*R, ["Ручка, Тетрадь", "Ручка, Тетрадь, Рюкзак, Пенал", "Рюкзак, Пенал", "Ручка"], 0,
      "DELETE FROM products WHERE stock < 10;\nSELECT name FROM products;", "products"),
    S(*R, ["Пенал | 10", "Пенал | 0", "10", ERR], 0,
      "UPDATE products SET stock = 10 WHERE stock = 0;\nSELECT name, stock FROM products WHERE id = 4;", "products"),
]

M5 = [
    S(*R, ["Айжан, Дамир, Алия, Дана", "Айжан, Алия, Дана", "Ерлан", "Дамир, Ерлан"], 0,
      "SELECT name FROM students WHERE city IN ('Актобе', 'Астана');", "students"),
    S(*R, ["Айжан, Дамир, Алия, Дана", "Дамир, Дана", "Айжан, Алия", "Ерлан"], 0,
      "SELECT name FROM students WHERE age BETWEEN 12 AND 13;", "students"),
    Q("Входят ли границы в BETWEEN 12 AND 13?", "BETWEEN 12 AND 13 шектері кіре ме?",
      [("Да, обе границы входят", "Иә, екі шегі де кіреді"), ("Нет", "Жоқ"), ("Только 12", "Тек 12"), ("Только 13", "Тек 13")], 0),
    S(*R, ["Кеша", "NULL", ("пусто", "бос"), "Барсик, Шарик, Мурка"], 0, "SELECT name FROM pets WHERE age IS NULL;", "pets"),
    S(*R, [("пусто", "бос"), "Кеша", "NULL", ERR], 0, "SELECT name FROM pets WHERE age = NULL;", "pets", out=""),
    Q("Как правильно проверить пустое значение?", "Бос мәнді қалай дұрыс тексереді?",
      ["age IS NULL", "age = NULL", "age == NULL", "age = ''"], 0),
    S(*R, ["3", "4", "10", "2"], 0, "SELECT COUNT(age) FROM pets;", "pets"),
    S(*R, ["4", "3", "10", "1"], 0, "SELECT COUNT(*) FROM pets;", "pets"),
    S(*R, ["3\n5\n0\n2", "3, 5, 0, 2", "3, 5, NULL, 2", "0"], 1, "SELECT COALESCE(age, 0) FROM pets;", "pets"),
    S(*R, ["Барсик | старый\nШарик | старый\nКеша | молодой\nМурка | молодой", "Барсик | старый\nШарик | старый\nКеша | NULL\nМурка | молодой",
           "старый, старый, молодой", "Барсик | старый"], 0,
      "SELECT name,\n  CASE WHEN age >= 3 THEN 'старый' ELSE 'молодой' END\nFROM pets;", "pets"),
    Q("Что делает CASE WHEN … THEN … ELSE … END?", "CASE WHEN … THEN … ELSE … END не істейді?",
      [("Выбирает значение по условию, как if", "if сияқты шарт бойынша мән таңдайды"), ("Создаёт таблицу", "Кесте жасайды"),
       ("Удаляет строки", "Жолдарды өшіреді"), ("Соединяет таблицы", "Кестелерді біріктіреді")], 0),
    S(*R, ["Барсик, Мурка", "Шарик", "Кеша", "Барсик, Шарик, Мурка"], 0, "SELECT name FROM pets WHERE kind IN ('кот');", "pets"),
    S(*R, ["Шарик, Кеша", "Барсик, Мурка", "Кеша", "Шарик"], 0, "SELECT name FROM pets WHERE kind NOT IN ('кот');", "pets"),
    S(*R, ["Ручка, Тетрадь, Пенал", "Ручка, Тетрадь", "Пенал", "Рюкзак"], 0,
      "SELECT name FROM products WHERE price BETWEEN 100 AND 1500;", "products"),
    S(*R, ["Айжан | хорошо\nАйжан | отлично", "Айжан | отлично\nАйжан | хорошо", "отлично, хорошо", "Айжан"], 1,
      "SELECT students.name,\n  CASE scores.score WHEN 5 THEN 'отлично' WHEN 4 THEN 'хорошо' ELSE 'плохо' END\nFROM scores JOIN students ON scores.student_id = students.id\nWHERE students.id = 1;", "students scores"),
    S(*R, ["2", "1", "3", "0"], 0, "SELECT COUNT(*) FROM pets WHERE age > 2;", "pets"),
    S(*R, ["Кеша | неизвестно", "Кеша | NULL", "неизвестно", "Кеша"], 0,
      "SELECT name, COALESCE(age, 'неизвестно') FROM pets WHERE id = 3;", "pets"),
    Q("Что вернёт 5 + NULL?", "5 + NULL не қайтарады?", ["NULL", "5", "0", ERR], 0),
    S(*R, ["есть, есть, есть, нет", "есть, нет", "4", "нет, нет, нет, есть"], 0,
      "SELECT CASE WHEN stock > 0 THEN 'есть' ELSE 'нет' END FROM products;", "products"),
    S(*R, ["3.33", "2.5", "3", "NULL"], 0, "SELECT ROUND(AVG(age), 2) FROM pets;", "pets"),
]

M6 = [
    S(*R, ["5", "6", "4", "Айжан"], 0, "SELECT LENGTH(name) FROM students WHERE id = 1;", "students"),
    S(*R, ["Айжан из Актобе", "Айжан Актобе", "Айжан||Актобе", ERR], 0,
      "SELECT name || ' из ' || city FROM students WHERE id = 1;", "students"),
    Q("Что делает || в SQLite?", "SQLite-тағы || не істейді?",
      [("Склеивает строки", "Жолдарды біріктіреді"), ("Логическое ИЛИ", "Логикалық НЕМЕСЕ"), ("Делит числа", "Сандарды бөледі"),
       ("Комментарий", "Түсініктеме")], 0),
    S(*R, ["Айж", "жан", "Ай", "йжа"], 0, "SELECT SUBSTR(name, 1, 3) FROM students WHERE id = 1;", "students"),
    S(*R, ["Дама", "Дамир", "Дамр", "Дaмир"], 0, "SELECT REPLACE(name, 'ир', 'а') FROM students WHERE id = 2;", "students"),
    S(*R, ["2", "2.5", "3", "2.0"], 0, "SELECT 5 / 2;", ""),
    S(*R, ["2.5", "2", "3", "2.0"], 0, "SELECT 5.0 / 2;", ""),
    S(*R, ["1", "2", "0", "2.5"], 0, "SELECT 5 % 2;", ""),
    S(*R, ["3.67", "3.6", "3.7", "4"], 0, "SELECT ROUND(11.0 / 3, 2);", ""),
    S(*R, ["Ручка | 6000\nТетрадь | 7500\nРюкзак | 27000\nПенал | 0", "6000, 7500, 27000, 0", "40500", "Ручка | 6000"], 0,
      "SELECT name, price * stock AS total FROM products;", "products"),
    S(*R, ["40500", "10650", "68", "4"], 0, "SELECT SUM(price * stock) FROM products;", "products"),
    S(*R, ["2662.5", "2662", "2663", "10650"], 0, "SELECT AVG(price) FROM products;", "products"),
    S(*R, ["5", "-5", "0", "NULL"], 0, "SELECT ABS(-5);", ""),
    S(*R, ["Айжан, Алия, Дамир, Дана, Ерлан", "Ерлан, Дана, Дамир, Алия, Айжан", "Айжан, Дамир, Ерлан, Алия, Дана", "Алия, Дана, Айжан, Дамир, Ерлан"], 2,
      "SELECT name FROM students ORDER BY LENGTH(name) DESC, name;", "students"),
    S(*R, ["4.5 | Айжан\n4 | Алия", "Айжан | 4.5\nАлия | 4\nДамир | 4\nДана | 4", "Айжан | 4.5\nДамир | 4\nДана | 4\nАлия | 4", "4.5"], 1,
      "SELECT students.name, ROUND(AVG(scores.score), 2) AS avg\nFROM scores JOIN students ON scores.student_id = students.id\nGROUP BY students.id\nORDER BY avg DESC, students.name;", "students scores"),
    Q("Почему 5 / 2 в SQLite даёт 2?", "SQLite-та 5 / 2 неге 2 береді?",
      [("Оба числа целые - деление целое", "Екі сан да бүтін - бөлу бүтін болады"), ("Это ошибка базы", "Бұл базаның қатесі"),
       ("SQLite округляет вверх", "SQLite жоғары қарай дөңгелектейді"), ("Так работает ORDER BY", "ORDER BY осылай жұмыс істейді")], 0),
    S(*R, ["Барсик (кот)", "Барсик кот", "Барсик(кот)", ERR], 0, "SELECT name || ' (' || kind || ')' FROM pets WHERE id = 1;", "pets"),
    S(*R, ["Ер", "ан", "Ерл", "лан"], 0, "SELECT SUBSTR(name, 1, 2) FROM students WHERE id = 4;", "students"),
    S(*R, ["180", "150", "165", "15"], 0, "SELECT price * 1.2 FROM products WHERE id = 1;", "products"),
    S(*R, ["3", "4", "5", "7"], 0, "SELECT LENGTH('SQL');", ""),
]

M7 = [
    S(*R, ["Айжан, Айжан, Дамир, Алия, Алия, Ерлан, Дана", "Айжан, Дамир, Алия, Дана", "Ерлан", "Айжан, Дамир, Алия, Ерлан, Дана"], 0,
      "SELECT students.name\nFROM students LEFT JOIN scores ON scores.student_id = students.id\nORDER BY students.id;", "students scores"),
    Q("Чем LEFT JOIN отличается от JOIN?", "LEFT JOIN мен JOIN айырмашылығы неде?",
      [("Оставляет все строки левой таблицы, даже без пары", "Сол кестенің барлық жолын, жұбы болмаса да, қалдырады"),
       ("Ничем", "Ешнәрсемен"), ("Соединяет только первые строки", "Тек бірінші жолдарды біріктіреді"),
       ("Работает только с числами", "Тек сандармен жұмыс істейді")], 0),
    S(*R, ["Ерлан | NULL", "Ерлан | 0", "Ерлан", ("пусто", "бос")], 0,
      "SELECT students.name, scores.score\nFROM students LEFT JOIN scores ON scores.student_id = students.id\nWHERE students.id = 4;", "students scores"),
    S(*R, ["Ерлан", "Дана", "Дамир", ("пусто", "бос")], 0,
      "SELECT students.name\nFROM students LEFT JOIN scores ON scores.student_id = students.id\nWHERE scores.score IS NULL;", "students scores"),
    S(*R, ["Дамир, Ерлан, Дана", "Ерлан", "Айжан, Алия", "Дамир, Дана"], 0,
      "SELECT name FROM students WHERE age > (SELECT AVG(age) FROM students);", "students"),
    S(*R, ["Айжан, Алия", "Айжан", "Алия, Дана", "Айжан, Алия, Дана"], 0,
      "SELECT name FROM students WHERE id IN (SELECT student_id FROM scores WHERE score = 5);", "students scores"),
    Q("Что такое подзапрос?", "Ішкі сұрау деген не?",
      [("SELECT внутри другого запроса в скобках", "Жақшадағы басқа сұрау ішіндегі SELECT"), ("Запрос без FROM", "FROM-сыз сұрау"),
       ("Комментарий", "Түсініктеме"), ("Вторая база данных", "Екінші деректер базасы")], 0),
    S(*R, ["Ерлан", "Айжан", "Дана", "Дамир"], 0,
      "SELECT name FROM students WHERE id NOT IN (SELECT student_id FROM scores);", "students scores"),
    S(*R, ["Рюкзак", "Пенал", "Ручка", "Тетрадь"], 0,
      "SELECT name FROM products WHERE price = (SELECT MAX(price) FROM products);", "products"),
    S(*R, ["Пенал", "Рюкзак", "Ручка", ("пусто", "бос")], 0,
      "SELECT products.name FROM products\nLEFT JOIN orders ON orders.product_id = products.id\nWHERE orders.id IS NULL;", "products orders"),
    S(*R, ["Ручка | 1050\nТетрадь | 900\nРюкзак | 9000", "Ручка | 750\nТетрадь | 900\nРюкзак | 9000", "10950", "Рюкзак | 9000"], 0,
      "SELECT products.name, SUM(orders.qty * products.price)\nFROM orders JOIN products ON orders.product_id = products.id\nGROUP BY products.id ORDER BY products.id;", "products orders"),
    S(*R, ["10950", "10650", "11", "9000"], 0,
      "SELECT SUM(orders.qty * products.price)\nFROM orders JOIN products ON orders.product_id = products.id;", "products orders"),
    S(*R, ["Ручка", "Тетрадь", "Рюкзак", "Пенал"], 0,
      "SELECT products.name FROM orders JOIN products ON orders.product_id = products.id\nGROUP BY products.id ORDER BY SUM(orders.qty) DESC LIMIT 1;", "products orders"),
    S(*R, ["Айжан | 2\nДамир | 1\nАлия | 2\nЕрлан | 0\nДана | 1", "Айжан | 2\nДамир | 1\nАлия | 2\nЕрлан | 1\nДана | 1",
           "Айжан | 2\nДамир | 1\nАлия | 2\nДана | 1", "6"], 0,
      "SELECT students.name, COUNT(scores.score)\nFROM students LEFT JOIN scores ON scores.student_id = students.id\nGROUP BY students.id ORDER BY students.id;", "students scores"),
    S(*R, ["2", "3", "1", "4"], 0, "SELECT COUNT(DISTINCT product_id) FROM orders WHERE qty > 1;", "orders"),
    S(*R, ["Айжан, Алия, Дана", "Дамир, Ерлан", "Дана", "Айжан"], 0,
      "SELECT name FROM students\nWHERE city = (SELECT city FROM students WHERE name = 'Дана');", "students"),
    Q("Какая таблица в LEFT JOIN считается «левой»?", "LEFT JOIN-да қай кесте «сол жақ» болып саналады?",
      [("Та, что написана после FROM", "FROM-нан кейін жазылғаны"), ("Та, что после LEFT JOIN", "LEFT JOIN-нан кейінгісі"),
       ("Та, где больше строк", "Жолы көп кесте"), ("Любая", "Кез келгені")], 0),
    S(*R, ["5", "4", "3", "6"], 0, "SELECT COUNT(*) FROM scores WHERE score > (SELECT MIN(score) FROM scores);", "scores"),
    S(*R, ["4.5", "4", "4.0", "5"], 0,
      "SELECT AVG(score) FROM scores WHERE student_id = (SELECT id FROM students WHERE name = 'Айжан');", "students scores"),
    S(*R, ["Тетрадь, Рюкзак", "Ручка", "Ручка, Тетрадь, Рюкзак", "Пенал"], 2,
      "SELECT name FROM products WHERE id IN (SELECT product_id FROM orders WHERE qty <= 3);", "products orders"),
]

M8 = [
    Q("Что значит PRIMARY KEY?", "PRIMARY KEY нені білдіреді?",
      [("Столбец с уникальным номером каждой строки", "Әр жолдың бірегей нөмірі бар баған"),
       ("Пароль к таблице", "Кестенің құпиясөзі"), ("Первая строка", "Бірінші жол"), ("Самый важный столбец для сортировки", "Сұрыптауға ең маңызды баған")], 0),
    Q("Что значит NOT NULL?", "NOT NULL нені білдіреді?",
      [("Значение обязательно, пустым быть не может", "Мән міндетті, бос бола алмайды"), ("Значение всегда 0", "Мән әрқашан 0"),
       ("Столбец удалён", "Баған өшірілген"), ("Значение уникально", "Мән бірегей")], 0),
    S(*R, ["5", "NULL", "0", ERR], 0,
      "CREATE TABLE games (id INTEGER PRIMARY KEY, title TEXT NOT NULL, rating INTEGER DEFAULT 5);\nINSERT INTO games (id, title) VALUES (1, 'Minecraft');\nSELECT rating FROM games;", ""),
    S("Что будет при выполнении?", "Орындағанда не болады?", [ERR, "1", "NULL", ("пусто", "бос")], 0,
      "CREATE TABLE games (id INTEGER PRIMARY KEY, title TEXT NOT NULL);\nINSERT INTO games (id) VALUES (1);", "", err=True),
    S("Что будет при выполнении?", "Орындағанда не болады?", [ERR, "2", "1", "NULL"], 0,
      "CREATE TABLE games (id INTEGER PRIMARY KEY, title TEXT);\nINSERT INTO games VALUES (1, 'Minecraft');\nINSERT INTO games VALUES (1, 'Roblox');", "", err=True),
    Q("Для чего DEFAULT?", "DEFAULT не үшін керек?",
      [("Значение по умолчанию, если его не указали", "Көрсетілмесе, әдепкі мән"), ("Удаляет столбец", "Бағанды өшіреді"),
       ("Сортирует", "Сұрыптайды"), ("Создаёт копию", "Көшірме жасайды")], 0),
    S(*R, ["NULL", ("пусто", "бос"), "0", ERR], 0,
      "ALTER TABLE students ADD COLUMN email TEXT;\nSELECT email FROM students WHERE id = 1;", "students"),
    S(*R, ["aizhan@mail.ru", "NULL", ERR, "Айжан"], 0,
      "ALTER TABLE students ADD COLUMN email TEXT;\nUPDATE students SET email = 'aizhan@mail.ru' WHERE id = 1;\nSELECT email FROM students WHERE id = 1;", "students"),
    Q("Какая команда добавляет новый столбец?", "Қай команда жаңа баған қосады?",
      ["ALTER TABLE … ADD COLUMN …", "INSERT COLUMN …", "UPDATE TABLE … ADD …", "CREATE COLUMN …"], 0),
    Q("Что делает DROP TABLE pets;?", "DROP TABLE pets; не істейді?",
      [("Удаляет всю таблицу вместе с данными", "Бүкіл кестені деректерімен бірге өшіреді"), ("Удаляет одну строку", "Бір жолды өшіреді"),
       ("Очищает только столбец", "Тек бағанды тазалайды"), ("Ничего", "Ештеңе")], 0),
    S("Что будет при выполнении?", "Орындағанда не болады?", [ERR, "0", "4", "NULL"], 0,
      "DROP TABLE pets;\nSELECT COUNT(*) FROM pets;", "pets", err=True),
    Q("Какой тип подходит для цены с копейками?", "Тиыны бар бағаға қай тип сәйкес?", ["REAL", "TEXT", "INTEGER", "DATE"], 0),
    Q("Зачем в таблице orders столбец product_id?", "orders кестесінде product_id бағаны не үшін?",
      [("Чтобы связать заказ с товаром из products", "Тапсырысты products-тағы тауармен байланыстыру үшін"),
       ("Для сортировки", "Сұрыптау үшін"), ("Это цена", "Бұл баға"), ("Он не нужен", "Ол керек емес")], 0),
    S(*R, ["Мурка", "Барсик", "Шарик", "Кеша"], 0,
      "ALTER TABLE pets RENAME TO animals;\nSELECT name FROM animals WHERE age = 2;", "pets"),
    S(*R, ["3", "4", "1", ERR], 0,
      "CREATE TABLE cities (name TEXT UNIQUE);\nINSERT INTO cities SELECT DISTINCT city FROM students;\nSELECT COUNT(*) FROM cities;", "students"),
    Q("Что значит UNIQUE у столбца?", "Бағандағы UNIQUE нені білдіреді?",
      [("Значения в нём не могут повторяться", "Ондағы мәндер қайталана алмайды"), ("Столбец один в таблице", "Кестеде бір ғана баған"),
       ("Значение обязательно", "Мән міндетті"), ("Значение - число", "Мән - сан")], 0),
    S(*R, ["Ручка | 5\nТетрадь | 3\nРучка | 2\nРюкзак | 1", "Ручка | 7\nТетрадь | 3\nРюкзак | 1", "11", "Ручка | 5"], 0,
      "SELECT products.name, orders.qty\nFROM orders JOIN products ON orders.product_id = products.id\nORDER BY orders.id;", "products orders"),
    S(*R, ["Рюкзак", "Ручка", "Тетрадь", "Пенал"], 0,
      "SELECT products.name FROM orders JOIN products ON orders.product_id = products.id\nORDER BY orders.qty * products.price DESC LIMIT 1;", "products orders"),
    S(*R, ["2", "1", "3", "4"], 0,
      "UPDATE products SET stock = stock - 3 WHERE id = 3;\nSELECT COUNT(*) FROM products WHERE stock = 0;", "products"),
    S(*R, ["Барсик, Мурка", "Барсик", "Мурка", "Шарик"], 0,
      "CREATE TABLE owners (pet_id INTEGER, owner TEXT);\nINSERT INTO owners VALUES (1, 'Аян'), (4, 'Аян'), (2, 'Дана');\nSELECT pets.name FROM pets JOIN owners ON owners.pet_id = pets.id\nWHERE owners.owner = 'Аян';", "pets"),
]

MODULES = {1: M1, 2: M2, 3: M3, 4: M4, 5: M5, 6: M6, 7: M7, 8: M8}

if __name__ == "__main__":
    build("SQL", "sql", MODULES, runner)
