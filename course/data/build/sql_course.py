"""Курс «SQL» для детей 12–15 лет: 24 урока, 8 модулей (модули 5–8 - в sql_course2.py). База - школа: ученики и оценки.

    python course/data/build/sql_course.py   → course/data/sql.json
Каждое задание проверяется на двух разных наборах данных; правильный ответ вычисляется
эталонным запросом во встроенном SQLite (тот же движок, что и на сайте - sql.js).
"""
import json
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = lambda ru, kk: {"p": [ru, kk]}
C = lambda code: {"code": code}

SCHEMA = """CREATE TABLE students (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, city TEXT, class TEXT);
CREATE TABLE scores (student_id INTEGER, subject TEXT, score INTEGER);
"""
DATA_A = SCHEMA + """INSERT INTO students VALUES
 (1,'Айжан',12,'Актобе','6А'),(2,'Дамир',13,'Астана','7Б'),(3,'Алия',12,'Актобе','6А'),(4,'Ерлан',14,'Алматы','8А'),
 (5,'Дана',13,'Актобе','7Б'),(6,'Тимур',11,'Астана','5В'),(7,'Аружан',14,'Актобе','8А'),(8,'Нурсултан',12,'Алматы','6А');
INSERT INTO scores VALUES
 (1,'Математика',5),(1,'Информатика',5),(1,'История',4),(2,'Математика',4),(2,'Информатика',5),(2,'История',3),
 (3,'Математика',3),(3,'Информатика',4),(4,'Математика',5),(4,'Информатика',4),(4,'История',5),(5,'Математика',4),
 (5,'История',4),(6,'Математика',3),(6,'Информатика',3),(7,'Информатика',5),(7,'История',5),(8,'Математика',4),(8,'Информатика',2);
"""
DATA_B = SCHEMA + """INSERT INTO students VALUES
 (1,'Мадина',13,'Атырау','7А'),(2,'Ислам',12,'Актобе','6Б'),(3,'Камила',15,'Шымкент','9А'),(4,'Арман',13,'Актобе','7А'),
 (5,'Сабина',12,'Атырау','6Б'),(6,'Бекзат',14,'Актобе','8Б');
INSERT INTO scores VALUES
 (1,'Математика',4),(1,'Информатика',5),(2,'Математика',5),(2,'История',3),(3,'Информатика',4),(3,'История',5),
 (4,'Математика',2),(4,'Информатика',3),(5,'История',4),(6,'Математика',5),(6,'Информатика',5),(6,'История',4);
"""
BOOKS = """CREATE TABLE books (id INTEGER PRIMARY KEY, title TEXT, author TEXT, year INTEGER, pages INTEGER);
INSERT INTO books VALUES (1,'Абай жолы','Мухтар Ауэзов',1942,600),(2,'Маленький принц','Антуан де Сент-Экзюпери',1943,96),
 (3,'Гарри Поттер','Джоан Роулинг',1997,400),(4,'Кочевники','Ильяс Есенберлин',1976,700);
"""
BOOKS_B = """CREATE TABLE books (id INTEGER PRIMARY KEY, title TEXT, author TEXT, year INTEGER, pages INTEGER);
INSERT INTO books VALUES (1,'Хоббит','Джон Толкин',1937,310),(2,'Буратино','Алексей Толстой',1936,150);
"""


def Q(title, text, hint, solution, starter="SELECT * FROM students;", ordered=False, after=None, data=(DATA_A, DATA_B)):
    t = {"kind": "sql", "title": title, "text": text, "hint": hint, "starter": starter, "solution": solution,
         "tests": [{"setup": d, "ordered": ordered} for d in data]}
    if after:
        for x in t["tests"]:
            x["after"] = after
    return t


TABLES = P("В базе две таблицы. students: id, name (имя), age (возраст), city (город), class (класс). scores: student_id (номер ученика), subject (предмет), score (оценка).",
           "Базада екі кесте бар. students: id, name (есім), age (жас), city (қала), class (сынып). scores: student_id (оқушы нөмірі), subject (пән), score (баға).")

MODULES = [
 {"number": 1, "title": ["Первые запросы", "Алғашқы сұраулар"], "lessons": [
  {"number": 1, "title": ["Что такое база данных", "Деректер базасы деген не"],
   "goal": ["Понять, что такое таблица, и получить из неё данные запросом SELECT.", "Кесте деген не екенін түсініп, SELECT сұрауымен одан дерек алу."],
   "theory": [
    P("База данных - это набор таблиц, как в Excel. SQL - язык, на котором у базы «спрашивают» данные. Такие базы есть у Kaspi, школ, игр и соцсетей.",
      "Деректер базасы - Excel сияқты кестелер жиыны. SQL - базадан дерек «сұрайтын» тіл. Мұндай базалар Kaspi-де, мектептерде, ойындарда және әлеуметтік желілерде бар."),
    C("SELECT * FROM students;\nSELECT name, age FROM students;"),
    P("SELECT * - все столбцы, SELECT name, age - только нужные. FROM - из какой таблицы. Нажми «Запустить», чтобы увидеть таблицу.",
      "SELECT * - барлық бағандар, SELECT name, age - тек керектері. FROM - қай кестеден. Кестені көру үшін «Іске қосу» батырмасын бас."),
    TABLES,
   ],
   "tasks": [
    Q(["Все ученики", "Барлық оқушылар"], ["Выведи всю таблицу students.", "students кестесін толық шығар."], ["SELECT * FROM students;", "SELECT * FROM students;"],
      "SELECT * FROM students;", starter=""),
    Q(["Только имена", "Тек есімдер"], ["Выведи только имена учеников.", "Тек оқушылардың есімдерін шығар."], ["SELECT name FROM …", "SELECT name FROM …"], "SELECT name FROM students;"),
    Q(["Имя и город", "Есім және қала"], ["Выведи имя и город каждого ученика.", "Әр оқушының есімі мен қаласын шығар."], ["SELECT name, city FROM students;", "SELECT name, city FROM students;"], "SELECT name, city FROM students;"),
    Q(["Все оценки", "Барлық бағалар"], ["Выведи всю таблицу scores.", "scores кестесін толық шығар."], ["FROM scores", "FROM scores"], "SELECT * FROM scores;"),
   ]},
  {"number": 2, "title": ["Условие WHERE", "WHERE шарты"],
   "goal": ["Научиться выбирать только нужные строки.", "Тек керекті жолдарды таңдауды үйрену."],
   "theory": [
    P("WHERE оставляет только строки, где условие верно. Текст пишут в одинарных кавычках: city = 'Актобе'.",
      "WHERE тек шарт ақиқат болатын жолдарды қалдырады. Мәтін бір тырнақшамен жазылады: city = 'Актобе'."),
    C("SELECT name FROM students WHERE city = 'Актобе';\nSELECT name, age FROM students WHERE age > 12;"),
    P("Сравнения: = > < >= <= и <> (не равно).", "Салыстырулар: = > < >= <= және <> (тең емес)."), TABLES,
   ],
   "tasks": [
    Q(["Из Актобе", "Ақтөбеден"], ["Выведи имена учеников из Актобе.", "Ақтөбедегі оқушылардың есімдерін шығар."], ["WHERE city = 'Актобе'", "WHERE city = 'Актобе'"], "SELECT name FROM students WHERE city = 'Актобе';"),
    Q(["Старше 12", "12-ден үлкен"], ["Выведи имена и возраст учеников старше 12 лет.", "12 жастан үлкен оқушылардың есімі мен жасын шығар."], ["WHERE age > 12", "WHERE age > 12"], "SELECT name, age FROM students WHERE age > 12;"),
    Q(["Пятёрки", "Бестіктер"], ["Выведи все строки таблицы scores, где оценка 5.", "scores кестесінің бағасы 5 болатын барлық жолдарын шығар."], ["FROM scores WHERE score = 5", "FROM scores WHERE score = 5"], "SELECT * FROM scores WHERE score = 5;", starter="SELECT * FROM scores;"),
    Q(["Не из Актобе", "Ақтөбеден емес"], ["Выведи имена учеников, которые живут не в Актобе.", "Ақтөбеде тұрмайтын оқушылардың есімдерін шығар."], ["<> значит «не равно»", "<> «тең емес» дегенді білдіреді"], "SELECT name FROM students WHERE city <> 'Актобе';"),
   ]},
  {"number": 3, "title": ["AND, OR и LIKE", "AND, OR және LIKE"],
   "goal": ["Научиться объединять условия и искать по части текста.", "Шарттарды біріктіруді және мәтін бөлігі бойынша іздеуді үйрену."],
   "theory": [
    P("AND - оба условия, OR - хотя бы одно. LIKE ищет по шаблону: 'А%' - начинается на А, '%ан' - заканчивается на «ан».",
      "AND - екі шарт та, OR - ең болмаса біреуі. LIKE үлгі бойынша іздейді: 'А%' - А-дан басталады, '%ан' - «ан»-мен аяқталады."),
    C("SELECT name FROM students WHERE city = 'Актобе' AND age = 12;\nSELECT name FROM students WHERE name LIKE 'А%';"), TABLES,
   ],
   "tasks": [
    Q(["Актобе и 12 лет", "Ақтөбе және 12 жас"], ["Выведи имена учеников из Актобе, которым 12 лет.", "Ақтөбедегі 12 жастағы оқушылардың есімдерін шығар."], ["… AND …", "… AND …"], "SELECT name FROM students WHERE city = 'Актобе' AND age = 12;"),
    Q(["Самые младшие и старшие", "Ең кішілер мен үлкендер"], ["Выведи имена учеников, которым меньше 12 или больше 13 лет.", "12-ден кіші немесе 13-тен үлкен оқушылардың есімдерін шығар."], ["… OR …", "… OR …"], "SELECT name FROM students WHERE age < 12 OR age > 13;"),
    Q(["На букву А", "А әрпіне"], ["Выведи имена, которые начинаются на букву А.", "А әрпінен басталатын есімдерді шығар."], ["name LIKE 'А%'", "name LIKE 'А%'"], "SELECT name FROM students WHERE name LIKE 'А%';"),
    Q(["Хорошие оценки по математике", "Математикадан жақсы бағалар"], ["Выведи student_id и оценку для математики, где оценка 4 или выше.", "Математикадан бағасы 4 немесе одан жоғары жолдардың student_id мен бағасын шығар."],
      ["subject = 'Математика' AND score >= 4", "subject = 'Математика' AND score >= 4"], "SELECT student_id, score FROM scores WHERE subject = 'Математика' AND score >= 4;", starter="SELECT * FROM scores;"),
   ]},
 ]},
 {"number": 2, "title": ["Сортировка и подсчёты", "Сұрыптау және санау"], "lessons": [
  {"number": 4, "title": ["ORDER BY и LIMIT", "ORDER BY және LIMIT"],
   "goal": ["Научиться сортировать строки и брать первые несколько.", "Жолдарды сұрыптауды және алғашқы бірнешеуін алуды үйрену."],
   "theory": [
    P("ORDER BY age - по возрастанию, ORDER BY age DESC - по убыванию. LIMIT 3 - только первые 3 строки.",
      "ORDER BY age - өсу ретімен, ORDER BY age DESC - кему ретімен. LIMIT 3 - тек алғашқы 3 жол."),
    C("SELECT name, age FROM students ORDER BY age DESC, name;\nSELECT name FROM students ORDER BY name LIMIT 3;"),
    P("Если значения одинаковые, можно добавить второй столбец сортировки через запятую - так порядок всегда понятен.", "Мәндер бірдей болса, үтір арқылы сұрыптаудың екінші бағанын қосуға болады - сонда рет әрқашан түсінікті."), TABLES,
   ],
   "tasks": [
    Q(["По алфавиту", "Әліпби бойынша"], ["Выведи имена учеников по алфавиту.", "Оқушылардың есімдерін әліпби бойынша шығар."], ["ORDER BY name", "ORDER BY name"], "SELECT name FROM students ORDER BY name;", ordered=True),
    Q(["От старших к младшим", "Үлкеннен кішіге"], ["Выведи имя и возраст: сначала старшие, при равном возрасте - по алфавиту.", "Есім мен жасты шығар: алдымен үлкендер, жасы бірдей болса - әліпби бойынша."], ["ORDER BY age DESC, name", "ORDER BY age DESC, name"], "SELECT name, age FROM students ORDER BY age DESC, name;", ordered=True),
    Q(["Три первых", "Алғашқы үшеуі"], ["Выведи первые три имени по алфавиту.", "Әліпби бойынша алғашқы үш есімді шығар."], ["ORDER BY name LIMIT 3", "ORDER BY name LIMIT 3"], "SELECT name FROM students ORDER BY name LIMIT 3;", ordered=True),
    Q(["Лучшие оценки", "Ең жақсы бағалар"], ["Выведи student_id, subject и score из scores по убыванию оценки; при равной оценке - по student_id, затем по предмету.", "scores-тан student_id, subject және score-ды бағаның кемуі бойынша шығар; бағасы бірдей болса - student_id, кейін пән бойынша."],
      ["ORDER BY score DESC, student_id, subject", "ORDER BY score DESC, student_id, subject"], "SELECT student_id, subject, score FROM scores ORDER BY score DESC, student_id, subject;", starter="SELECT * FROM scores;", ordered=True),
   ]},
  {"number": 5, "title": ["Подсчёты: COUNT, AVG, MAX", "Санау: COUNT, AVG, MAX"],
   "goal": ["Научиться считать количество, сумму, среднее, минимум и максимум.", "Санды, қосындыны, орташаны, минимум мен максимумды есептеуді үйрену."],
   "theory": [
    P("COUNT(*) - сколько строк, SUM - сумма, AVG - среднее, MIN и MAX - наименьшее и наибольшее.",
      "COUNT(*) - жолдар саны, SUM - қосынды, AVG - орташа, MIN және MAX - ең кіші және ең үлкен."),
    C("SELECT COUNT(*) FROM students;\nSELECT AVG(score), MAX(score) FROM scores WHERE subject = 'Математика';"), TABLES,
   ],
   "tasks": [
    Q(["Сколько учеников", "Неше оқушы"], ["Выведи, сколько всего учеников.", "Барлығы неше оқушы бар екенін шығар."], ["SELECT COUNT(*) FROM students;", "SELECT COUNT(*) FROM students;"], "SELECT COUNT(*) FROM students;"),
    Q(["Сколько из Актобе", "Ақтөбеден нешеу"], ["Выведи, сколько учеников из Актобе.", "Ақтөбеден неше оқушы бар екенін шығар."], ["COUNT(*) … WHERE …", "COUNT(*) … WHERE …"], "SELECT COUNT(*) FROM students WHERE city = 'Актобе';"),
    Q(["Средний возраст", "Орташа жас"], ["Выведи средний возраст учеников.", "Оқушылардың орташа жасын шығар."], ["AVG(age)", "AVG(age)"], "SELECT AVG(age) FROM students;"),
    Q(["Самый старший и младший", "Ең үлкен және кіші"], ["Выведи максимальный и минимальный возраст.", "Ең үлкен және ең кіші жасты шығар."], ["MAX(age), MIN(age)", "MAX(age), MIN(age)"], "SELECT MAX(age), MIN(age) FROM students;"),
   ]},
  {"number": 6, "title": ["DISTINCT и AS", "DISTINCT және AS"],
   "goal": ["Научиться убирать повторы и давать столбцам понятные имена.", "Қайталауларды алып тастауды және бағандарға түсінікті атау беруді үйрену."],
   "theory": [
    P("DISTINCT убирает одинаковые строки. AS даёт столбцу новое имя. Можно считать прямо в запросе: age + 1.",
      "DISTINCT бірдей жолдарды алып тастайды. AS бағанға жаңа атау береді. Сұраудың ішінде есептеуге болады: age + 1."),
    C("SELECT DISTINCT city FROM students;\nSELECT name, age + 1 AS next_year FROM students;"), TABLES,
   ],
   "tasks": [
    Q(["Города", "Қалалар"], ["Выведи список городов без повторов.", "Қалалар тізімін қайталаусыз шығар."], ["SELECT DISTINCT city …", "SELECT DISTINCT city …"], "SELECT DISTINCT city FROM students;"),
    Q(["Через год", "Бір жылдан кейін"], ["Выведи имя и возраст через год в столбце next_year.", "Есім мен бір жылдан кейінгі жасты next_year бағанында шығар."], ["age + 1 AS next_year", "age + 1 AS next_year"], "SELECT name, age + 1 AS next_year FROM students;"),
    Q(["Сколько городов", "Неше қала"], ["Выведи, сколько разных городов в таблице.", "Кестеде неше түрлі қала бар екенін шығар."], ["COUNT(DISTINCT city)", "COUNT(DISTINCT city)"], "SELECT COUNT(DISTINCT city) FROM students;"),
    Q(["Предметы", "Пәндер"], ["Выведи список предметов из scores без повторов, по алфавиту.", "scores-тағы пәндер тізімін қайталаусыз, әліпби бойынша шығар."], ["DISTINCT subject … ORDER BY subject", "DISTINCT subject … ORDER BY subject"],
      "SELECT DISTINCT subject FROM scores ORDER BY subject;", starter="SELECT * FROM scores;", ordered=True),
   ]},
 ]},
 {"number": 3, "title": ["Группировка и связи", "Топтау және байланыстар"], "lessons": [
  {"number": 7, "title": ["GROUP BY", "GROUP BY"],
   "goal": ["Научиться считать итоги по группам.", "Топтар бойынша қорытынды есептеуді үйрену."],
   "theory": [
    P("GROUP BY city собирает строки с одинаковым городом в группы, а COUNT, AVG, MAX считают по каждой группе отдельно.",
      "GROUP BY city қаласы бірдей жолдарды топтарға жинайды, ал COUNT, AVG, MAX әр топ бойынша жеке есептейді."),
    C("SELECT city, COUNT(*) FROM students GROUP BY city;\nSELECT subject, AVG(score) FROM scores GROUP BY subject;"), TABLES,
   ],
   "tasks": [
    Q(["Учеников по городам", "Қалалар бойынша оқушылар"], ["Выведи город и количество учеников в нём.", "Қаланы және ондағы оқушылар санын шығар."], ["GROUP BY city", "GROUP BY city"], "SELECT city, COUNT(*) FROM students GROUP BY city;"),
    Q(["Средняя по предметам", "Пәндер бойынша орташа"], ["Выведи предмет и среднюю оценку по нему.", "Пәнді және ол бойынша орташа бағаны шығар."], ["GROUP BY subject", "GROUP BY subject"], "SELECT subject, AVG(score) FROM scores GROUP BY subject;", starter="SELECT * FROM scores;"),
    Q(["Сколько оценок у ученика", "Оқушыда неше баға"], ["Выведи student_id и количество его оценок.", "student_id мен оның бағалар санын шығар."], ["GROUP BY student_id", "GROUP BY student_id"], "SELECT student_id, COUNT(*) FROM scores GROUP BY student_id;", starter="SELECT * FROM scores;"),
    Q(["Лучшая оценка ученика", "Оқушының ең жақсы бағасы"], ["Выведи student_id и его лучшую оценку.", "student_id мен оның ең жақсы бағасын шығар."], ["MAX(score) … GROUP BY student_id", "MAX(score) … GROUP BY student_id"], "SELECT student_id, MAX(score) FROM scores GROUP BY student_id;", starter="SELECT * FROM scores;"),
   ]},
  {"number": 8, "title": ["HAVING", "HAVING"],
   "goal": ["Научиться отбирать группы по условию.", "Топтарды шарт бойынша іріктеуді үйрену."],
   "theory": [
    P("WHERE фильтрует строки до группировки, а HAVING - группы после неё. Например, города, где больше одного ученика.",
      "WHERE жолдарды топтауға дейін, ал HAVING топтарды одан кейін сүзеді. Мысалы, бірден көп оқушысы бар қалалар."),
    C("SELECT city, COUNT(*) FROM students GROUP BY city HAVING COUNT(*) > 1;"), TABLES,
   ],
   "tasks": [
    Q(["Большие города", "Үлкен қалалар"], ["Выведи города, где больше одного ученика, и их количество.", "Бірден көп оқушысы бар қалаларды және олардың санын шығар."], ["HAVING COUNT(*) > 1", "HAVING COUNT(*) > 1"], "SELECT city, COUNT(*) FROM students GROUP BY city HAVING COUNT(*) > 1;"),
    Q(["Отличники", "Үздіктер"], ["Выведи student_id учеников, у которых средняя оценка 4.5 или выше.", "Орташа бағасы 4.5 немесе одан жоғары оқушылардың student_id-ін шығар."], ["HAVING AVG(score) >= 4.5", "HAVING AVG(score) >= 4.5"], "SELECT student_id FROM scores GROUP BY student_id HAVING AVG(score) >= 4.5;", starter="SELECT * FROM scores;"),
    Q(["Три оценки", "Үш баға"], ["Выведи student_id тех, у кого ровно три оценки.", "Дәл үш бағасы бар оқушылардың student_id-ін шығар."], ["HAVING COUNT(*) = 3", "HAVING COUNT(*) = 3"], "SELECT student_id FROM scores GROUP BY student_id HAVING COUNT(*) = 3;", starter="SELECT * FROM scores;"),
    Q(["Сложные предметы", "Қиын пәндер"], ["Выведи предметы, где самая низкая оценка меньше 4.", "Ең төменгі бағасы 4-тен кіші пәндерді шығар."], ["HAVING MIN(score) < 4", "HAVING MIN(score) < 4"], "SELECT subject FROM scores GROUP BY subject HAVING MIN(score) < 4;", starter="SELECT * FROM scores;"),
   ]},
  {"number": 9, "title": ["JOIN: соединяем таблицы", "JOIN: кестелерді біріктіру"],
   "goal": ["Научиться соединять две таблицы по общему столбцу.", "Екі кестені ортақ баған бойынша біріктіруді үйрену."],
   "theory": [
    P("В scores есть только номер ученика. Чтобы увидеть имя, таблицы соединяют: JOIN … ON scores.student_id = students.id.",
      "scores-та тек оқушы нөмірі бар. Есімді көру үшін кестелерді біріктіреді: JOIN … ON scores.student_id = students.id."),
    C("SELECT students.name, scores.subject, scores.score\nFROM scores JOIN students ON scores.student_id = students.id;"), TABLES,
   ],
   "tasks": [
    Q(["Имена и оценки", "Есімдер мен бағалар"], ["Выведи имя ученика, предмет и оценку для всех оценок.", "Барлық бағалар үшін оқушы есімін, пәнді және бағаны шығар."], ["JOIN students ON scores.student_id = students.id", "JOIN students ON scores.student_id = students.id"],
      "SELECT students.name, scores.subject, scores.score FROM scores JOIN students ON scores.student_id = students.id;"),
    Q(["Кто получил пятёрки", "Кім бестік алды"], ["Выведи имя и предмет для всех пятёрок.", "Барлық бестіктер үшін есім мен пәнді шығар."], ["JOIN … WHERE scores.score = 5", "JOIN … WHERE scores.score = 5"],
      "SELECT students.name, scores.subject FROM scores JOIN students ON scores.student_id = students.id WHERE scores.score = 5;"),
    Q(["Средний балл по именам", "Есімдер бойынша орташа балл"], ["Выведи имя и среднюю оценку каждого ученика, у которого есть оценки.", "Бағасы бар әр оқушының есімі мен орташа бағасын шығар."], ["JOIN … GROUP BY students.id", "JOIN … GROUP BY students.id"],
      "SELECT students.name, AVG(scores.score) FROM scores JOIN students ON scores.student_id = students.id GROUP BY students.id;"),
    Q(["Оценки из Актобе", "Ақтөбе бағалары"], ["Выведи имя, предмет и оценку только для учеников из Актобе.", "Тек Ақтөбедегі оқушылар үшін есімді, пәнді және бағаны шығар."], ["JOIN … WHERE students.city = 'Актобе'", "JOIN … WHERE students.city = 'Актобе'"],
      "SELECT students.name, scores.subject, scores.score FROM scores JOIN students ON scores.student_id = students.id WHERE students.city = 'Актобе';"),
   ]},
 ]},
 {"number": 4, "title": ["Создаём и меняем данные", "Деректерді жасау және өзгерту"], "lessons": [
  {"number": 10, "title": ["INSERT: добавляем строки", "INSERT: жолдар қосу"],
   "goal": ["Научиться добавлять новые строки в таблицу.", "Кестеге жаңа жолдар қосуды үйрену."],
   "theory": [
    P("INSERT INTO таблица (столбцы) VALUES (значения); - добавляет строку. Проверка потом сама посмотрит таблицу.",
      "INSERT INTO кесте (бағандар) VALUES (мәндер); - жол қосады. Тексеру кейін кестені өзі қарайды."),
    C("INSERT INTO students (id, name, age, city, class) VALUES (100, 'Ты', 12, 'Актобе', '6А');\nSELECT * FROM students;"), TABLES,
   ],
   "tasks": [
    Q(["Новый ученик", "Жаңа оқушы"], ["Добавь ученика: id 100, имя Мирас, 12 лет, город Актобе, класс 6А.", "Оқушы қос: id 100, есімі Мирас, 12 жас, Ақтөбе қаласы, 6А сыныбы."], ["INSERT INTO students VALUES (…);", "INSERT INTO students VALUES (…);"],
      "INSERT INTO students (id, name, age, city, class) VALUES (100, 'Мирас', 12, 'Актобе', '6А');", starter="", after="SELECT * FROM students WHERE id = 100;"),
    Q(["Оценка новому", "Жаңаға баға"], ["Добавь в scores оценку 5 по Информатике ученику с id 1.", "scores-қа id 1 оқушыға Информатикадан 5 баға қос."], ["INSERT INTO scores VALUES (1, 'Информатика', 5);", "INSERT INTO scores VALUES (1, 'Информатика', 5);"],
      "INSERT INTO scores VALUES (1, 'Информатика', 5);", starter="", after="SELECT COUNT(*) FROM scores WHERE student_id = 1 AND subject = 'Информатика' AND score = 5;"),
    Q(["Двое сразу", "Екеуі бірден"], ["Добавь двух учеников одним запросом: (101, 'Аян', 11, 'Астана', '5В') и (102, 'Асель', 13, 'Алматы', '7Б').", "Бір сұраумен екі оқушы қос: (101, 'Аян', 11, 'Астана', '5В') және (102, 'Асель', 13, 'Алматы', '7Б')."],
      ["VALUES (…), (…);", "VALUES (…), (…);"], "INSERT INTO students VALUES (101, 'Аян', 11, 'Астана', '5В'), (102, 'Асель', 13, 'Алматы', '7Б');", starter="", after="SELECT name FROM students WHERE id > 100;"),
    Q(["Своя таблица", "Өз кестең"], ["Создай таблицу pets (name TEXT, kind TEXT) и добавь в неё кота Барсика: ('Барсик', 'кот').", "pets (name TEXT, kind TEXT) кестесін жасап, оған Барсик мысығын қос: ('Барсик', 'кот')."],
      ["CREATE TABLE pets (name TEXT, kind TEXT); INSERT INTO pets VALUES (…);", "CREATE TABLE pets (name TEXT, kind TEXT); INSERT INTO pets VALUES (…);"],
      "CREATE TABLE pets (name TEXT, kind TEXT);\nINSERT INTO pets VALUES ('Барсик', 'кот');", starter="", after="SELECT * FROM pets;"),
   ]},
  {"number": 11, "title": ["UPDATE и DELETE", "UPDATE және DELETE"],
   "goal": ["Научиться изменять и удалять строки.", "Жолдарды өзгертуді және жоюды үйрену."],
   "theory": [
    P("UPDATE таблица SET столбец = значение WHERE условие; - меняет данные. DELETE FROM таблица WHERE условие; - удаляет. Без WHERE изменятся все строки - будь осторожен!",
      "UPDATE кесте SET баған = мән WHERE шарт; - деректерді өзгертеді. DELETE FROM кесте WHERE шарт; - жояды. WHERE болмаса, барлық жол өзгереді - абай бол!"),
    C("UPDATE students SET age = 13 WHERE id = 1;\nDELETE FROM scores WHERE score < 3;"), TABLES,
   ],
   "tasks": [
    Q(["День рождения", "Туған күн"], ["У ученика с id 1 день рождения: увеличь его возраст на 1.", "id 1 оқушының туған күні: оның жасын 1-ге арттыр."], ["UPDATE students SET age = age + 1 WHERE id = 1;", "UPDATE students SET age = age + 1 WHERE id = 1;"],
      "UPDATE students SET age = age + 1 WHERE id = 1;", starter="", after="SELECT id, age FROM students ORDER BY id;"),
    Q(["Переезд", "Көшу"], ["Ученик с id 2 переехал в Актобе. Обнови его город.", "id 2 оқушы Ақтөбеге көшті. Оның қаласын жаңарт."], ["UPDATE … SET city = 'Актобе' WHERE id = 2;", "UPDATE … SET city = 'Актобе' WHERE id = 2;"],
      "UPDATE students SET city = 'Актобе' WHERE id = 2;", starter="", after="SELECT id, city FROM students ORDER BY id;"),
    Q(["Убрать двойки", "Екіліктерді алып тастау"], ["Удали из scores все оценки ниже 3.", "scores-тан 3-тен төмен барлық бағаны жой."], ["DELETE FROM scores WHERE score < 3;", "DELETE FROM scores WHERE score < 3;"],
      "DELETE FROM scores WHERE score < 3;", starter="", after="SELECT COUNT(*), MIN(score) FROM scores;"),
    Q(["Всем по баллу", "Бәріне бір балл"], ["Учитель добавил всем по 1 баллу за Историю, но не выше 5. Обнови оценки по Истории, которые меньше 5.", "Мұғалім Тарихтан бәріне 1 балл қосты, бірақ 5-тен жоғары емес. Тарихтан 5-тен кіші бағаларды жаңарт."],
      ["SET score = score + 1 WHERE subject = 'История' AND score < 5", "SET score = score + 1 WHERE subject = 'История' AND score < 5"],
      "UPDATE scores SET score = score + 1 WHERE subject = 'История' AND score < 5;", starter="", after="SELECT student_id, score FROM scores WHERE subject = 'История' ORDER BY student_id;"),
   ]},
  {"number": 12, "title": ["Итоговый проект «Библиотека»", "Қорытынды жоба «Кітапхана»"], "project": True,
   "goal": ["Поработать с базой библиотеки: запросы, подсчёты, изменения.", "Кітапхана базасымен жұмыс істеу: сұраулар, санау, өзгерістер."],
   "theory": [
    P("В итоговом проекте другая база - библиотека. Таблица books: id, title (название), author (автор), year (год), pages (страницы).",
      "Қорытынды жобада басқа база - кітапхана. books кестесі: id, title (атауы), author (авторы), year (жылы), pages (беттері)."),
    C("SELECT title, year FROM books ORDER BY year;\nSELECT COUNT(*) FROM books WHERE pages > 300;"),
   ],
   "tasks": [
    Q(["Все книги по годам", "Жыл бойынша кітаптар"], ["Выведи название и год всех книг по возрастанию года.", "Барлық кітаптың атауы мен жылын жыл өсуі бойынша шығар."], ["ORDER BY year", "ORDER BY year"],
      "SELECT title, year FROM books ORDER BY year;", starter="SELECT * FROM books;", ordered=True, data=(BOOKS, BOOKS_B)),
    Q(["Толстые книги", "Қалың кітаптар"], ["Выведи названия книг больше 300 страниц.", "300 беттен көп кітаптардың атауларын шығар."], ["WHERE pages > 300", "WHERE pages > 300"],
      "SELECT title FROM books WHERE pages > 300;", starter="SELECT * FROM books;", data=(BOOKS, BOOKS_B)),
    Q(["Статистика", "Статистика"], ["Выведи количество книг и среднее число страниц.", "Кітаптар саны мен беттердің орташа санын шығар."], ["COUNT(*), AVG(pages)", "COUNT(*), AVG(pages)"],
      "SELECT COUNT(*), AVG(pages) FROM books;", starter="SELECT * FROM books;", data=(BOOKS, BOOKS_B)),
    Q(["Новая книга", "Жаңа кітап"], ["Добавь книгу: id 50, «Мой первый код», автор - ты (любое имя не важно, но впиши 'Я'), 2026 год, 120 страниц.", "Кітап қос: id 50, «Мой первый код», авторы - сен ('Я' деп жаз), 2026 жыл, 120 бет."],
      ["INSERT INTO books VALUES (50, 'Мой первый код', 'Я', 2026, 120);", "INSERT INTO books VALUES (50, 'Мой первый код', 'Я', 2026, 120);"],
      "INSERT INTO books VALUES (50, 'Мой первый код', 'Я', 2026, 120);", starter="", after="SELECT title, year, pages FROM books WHERE id = 50;", data=(BOOKS, BOOKS_B)),
    Q(["Итоговый запрос", "Қорытынды сұрау"], ["Выведи автора и количество его книг, только для авторов, у которых книги толще 100 страниц, по алфавиту авторов.", "Тек 100 беттен қалың кітаптары бар авторлар үшін авторды және оның кітаптар санын авторлардың әліпбиі бойынша шығар."],
      ["WHERE pages > 100 GROUP BY author ORDER BY author", "WHERE pages > 100 GROUP BY author ORDER BY author"],
      "SELECT author, COUNT(*) FROM books WHERE pages > 100 GROUP BY author ORDER BY author;", starter="SELECT * FROM books;", ordered=True, data=(BOOKS, BOOKS_B)),
   ]},
 ]},
]

COURSE = {"slug": "sql", "kind": "sql", "title": ["SQL", "SQL"],
          "desc": ["24 урока: как сайты и приложения хранят данные и что у них можно «спросить»", "24 сабақ: сайттар мен қосымшалар деректерді қалай сақтайды және олардан не «сұрауға» болады"],
          "color": "#8ED1C6", "order": 4}


def run(setup, code, after=None):
    db = sqlite3.connect(":memory:")
    db.executescript(setup)
    if after:
        db.executescript(code)
        cur = db.execute(after)
    else:
        cur = db.execute(code.strip().rstrip(";"))
    cols = [d[0] for d in cur.description] if cur.description else []
    rows = [[int(v) if isinstance(v, float) and v.is_integer() else v for v in r] for r in cur.fetchall()]
    db.close()
    return {"columns": cols, "rows": rows}


def main():
    import sys
    global MODULES
    sys.path.insert(0, str(HERE))
    from sql_course2 import MODULES2
    MODULES = MODULES + MODULES2
    n = 0
    for m in MODULES:
        for l in m["lessons"]:
            for t in l["tasks"]:
                n += 1
                for test in t["tests"]:
                    test["expected"] = run(test["setup"], t["solution"], test.get("after"))
                    if not test["expected"]["rows"]:
                        raise SystemExit(f"Пустой ответ: урок {l['number']} «{t['title'][0]}»")
                # начальный код не должен давать правильный ответ
                st = t["starter"].strip()
                if st:
                    try:
                        got = run(t["tests"][0]["setup"], st, t["tests"][0].get("after"))
                        if got["rows"] == t["tests"][0]["expected"]["rows"]:
                            raise SystemExit(f"Начальный код уже правильный: урок {l['number']} «{t['title'][0]}»")
                    except sqlite3.Error:
                        pass
    out = HERE.parent / "sql.json"
    out.write_text(json.dumps({"course": COURSE, "modules": MODULES}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Записано {out}: уроков {sum(len(m['lessons']) for m in MODULES)}, заданий {n}")


if __name__ == "__main__":
    main()
