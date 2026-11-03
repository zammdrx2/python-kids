"""Курс «SQL», модули 5–8 (уроки 13–24)."""
from sql_course import BOOKS, BOOKS_B, C, DATA_A, DATA_B, P, Q, TABLES

# Данные с пропусками (NULL) и ученик без оценок - для уроков про NULL и LEFT JOIN
NULLS = "\nUPDATE students SET city = NULL WHERE id IN (2, 5);\nINSERT INTO students VALUES (20, 'Новенький', 12, NULL, '6А');\n"
DN = (DATA_A + NULLS, DATA_B + NULLS)

SHOP = """CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, category TEXT, price INTEGER, stock INTEGER);
CREATE TABLE orders (id INTEGER PRIMARY KEY, product_id INTEGER, qty INTEGER, day TEXT);
INSERT INTO products VALUES (1,'Тетрадь','Канцелярия',150,100),(2,'Ручка','Канцелярия',90,250),(3,'Рюкзак','Сумки',9500,12),
 (4,'Пенал','Сумки',2100,30),(5,'Наушники','Техника',7800,8),(6,'Мышка','Техника',4500,0);
INSERT INTO orders VALUES (1,1,10,'пн'),(2,2,5,'пн'),(3,3,1,'вт'),(4,1,4,'вт'),(5,5,2,'ср'),(6,4,1,'ср'),(7,2,20,'чт');
"""
SHOP_B = """CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, category TEXT, price INTEGER, stock INTEGER);
CREATE TABLE orders (id INTEGER PRIMARY KEY, product_id INTEGER, qty INTEGER, day TEXT);
INSERT INTO products VALUES (1,'Альбом','Канцелярия',600,40),(2,'Сумка','Сумки',5000,5),(3,'Колонка','Техника',12000,3),(4,'Карандаш','Канцелярия',60,0);
INSERT INTO orders VALUES (1,1,3,'пн'),(2,3,1,'пн'),(3,1,2,'пт'),(4,2,1,'сб');
"""
DS = (SHOP, SHOP_B)
SHOP_T = P("База магазина. products: id, name (товар), category (категория), price (цена), stock (на складе). orders: id, product_id (номер товара), qty (количество), day (день).",
           "Дүкен базасы. products: id, name (тауар), category (санат), price (баға), stock (қоймада). orders: id, product_id (тауар нөмірі), qty (саны), day (күн).")

MODULES2 = [
 {"number": 5, "title": ["Продвинутые условия", "Күрделі шарттар"], "lessons": [
  {"number": 13, "title": ["IN и BETWEEN", "IN және BETWEEN"],
   "goal": ["Научиться коротко писать условия со списком и диапазоном.", "Тізім мен аралықпен шарттарды қысқа жазуды үйрену."],
   "theory": [
    P("IN ('Актобе', 'Астана') - значение из списка. BETWEEN 12 AND 13 - от 12 до 13 включительно. NOT IN - не из списка.",
      "IN ('Актобе', 'Астана') - тізімдегі мән. BETWEEN 12 AND 13 - 12-ден 13-ке дейін (қоса). NOT IN - тізімде жоқ."),
    C("SELECT name FROM students WHERE city IN ('Актобе', 'Астана');\nSELECT name FROM students WHERE age BETWEEN 12 AND 13;"), TABLES,
   ],
   "tasks": [
    Q(["Два города", "Екі қала"], ["Выведи имена учеников из Актобе или Астаны (используй IN).", "Ақтөбе немесе Астанадағы оқушылардың есімдерін шығар (IN қолдан)."], ["city IN ('Актобе', 'Астана')", "city IN ('Актобе', 'Астана')"], "SELECT name FROM students WHERE city IN ('Актобе', 'Астана');"),
    Q(["От 12 до 13", "12-ден 13-ке дейін"], ["Выведи имя и возраст учеников от 12 до 13 лет.", "12-ден 13 жасқа дейінгі оқушылардың есімі мен жасын шығар."], ["age BETWEEN 12 AND 13", "age BETWEEN 12 AND 13"], "SELECT name, age FROM students WHERE age BETWEEN 12 AND 13;"),
    Q(["Не эти предметы", "Бұл пәндер емес"], ["Выведи все оценки, кроме математики и информатики.", "Математика мен информатикадан басқа барлық бағаларды шығар."], ["subject NOT IN (…)", "subject NOT IN (…)"], "SELECT * FROM scores WHERE subject NOT IN ('Математика', 'Информатика');", starter="SELECT * FROM scores;"),
    Q(["Хорошисты", "Жақсы оқитындар"], ["Выведи student_id и предмет для оценок 4 и 5 (BETWEEN).", "4 және 5 бағалар үшін student_id мен пәнді шығар (BETWEEN)."], ["score BETWEEN 4 AND 5", "score BETWEEN 4 AND 5"], "SELECT student_id, subject FROM scores WHERE score BETWEEN 4 AND 5;", starter="SELECT * FROM scores;"),
   ]},
  {"number": 14, "title": ["Пустые значения NULL", "Бос мәндер NULL"],
   "goal": ["Понять, что такое NULL, и научиться с ним работать.", "NULL деген не екенін түсініп, онымен жұмыс істеуді үйрену."],
   "theory": [
    P("NULL - «значение неизвестно». Его нельзя сравнить через =, нужно IS NULL или IS NOT NULL. COALESCE(city, 'не указан') подставляет запасное значение.",
      "NULL - «мәні белгісіз». Оны = арқылы салыстыруға болмайды, IS NULL немесе IS NOT NULL керек. COALESCE(city, 'не указан') қосалқы мән қояды."),
    C("SELECT name FROM students WHERE city IS NULL;\nSELECT name, COALESCE(city, 'не указан') FROM students;"),
    P("В этом уроке у некоторых учеников город не указан.", "Бұл сабақта кейбір оқушылардың қаласы көрсетілмеген."),
   ],
   "tasks": [
    Q(["Без города", "Қаласыз"], ["Выведи имена учеников, у которых город не указан.", "Қаласы көрсетілмеген оқушылардың есімдерін шығар."], ["city IS NULL", "city IS NULL"], "SELECT name FROM students WHERE city IS NULL;", data=DN),
    Q(["С городом", "Қаласымен"], ["Выведи имя и город тех, у кого город указан.", "Қаласы көрсетілгендердің есімі мен қаласын шығар."], ["city IS NOT NULL", "city IS NOT NULL"], "SELECT name, city FROM students WHERE city IS NOT NULL;", data=DN),
    Q(["Запасное значение", "Қосалқы мән"], ["Выведи имя и город, а вместо пустого города - не указан.", "Есім мен қаланы шығар, ал бос қаланың орнына - не указан."], ["COALESCE(city, 'не указан')", "COALESCE(city, 'не указан')"], "SELECT name, COALESCE(city, 'не указан') FROM students;", data=DN),
    Q(["Сколько без города", "Қаласыздар нешеу"], ["Выведи, сколько учеников без города.", "Қаласыз неше оқушы бар екенін шығар."], ["COUNT(*) … WHERE city IS NULL", "COUNT(*) … WHERE city IS NULL"], "SELECT COUNT(*) FROM students WHERE city IS NULL;", data=DN),
   ]},
  {"number": 15, "title": ["CASE: если - то", "CASE: егер - онда"],
   "goal": ["Научиться выводить разные значения в зависимости от условия.", "Шартқа байланысты әртүрлі мәндерді шығаруды үйрену."],
   "theory": [
    P("CASE WHEN условие THEN значение … ELSE значение END - как if прямо в запросе.", "CASE WHEN шарт THEN мән … ELSE мән END - сұраудың ішіндегі if сияқты."),
    C("SELECT name,\n  CASE WHEN age >= 13 THEN 'старший' ELSE 'младший' END AS grp\nFROM students;"), TABLES,
   ],
   "tasks": [
    Q(["Старшие и младшие", "Үлкендер мен кішілер"], ["Выведи имя и группу: старший для 13 лет и больше, иначе младший.", "Есім мен топты шығар: 13 және одан үлкендерге старший, әйтпесе младший."], ["CASE WHEN age >= 13 THEN 'старший' ELSE 'младший' END", "CASE WHEN age >= 13 THEN 'старший' ELSE 'младший' END"],
      "SELECT name, CASE WHEN age >= 13 THEN 'старший' ELSE 'младший' END FROM students;"),
    Q(["Оценка словами", "Баға сөзбен"], ["Выведи student_id, предмет и оценку словами: 5 - отлично, 4 - хорошо, иначе - средне.", "student_id, пәнді және бағаны сөзбен шығар: 5 - отлично, 4 - хорошо, әйтпесе - средне."],
      ["CASE WHEN score = 5 THEN … WHEN score = 4 THEN … ELSE … END", "CASE WHEN score = 5 THEN … WHEN score = 4 THEN … ELSE … END"],
      "SELECT student_id, subject, CASE WHEN score = 5 THEN 'отлично' WHEN score = 4 THEN 'хорошо' ELSE 'средне' END FROM scores;", starter="SELECT * FROM scores;"),
    Q(["Местные", "Жергілікті"], ["Выведи имя и местный для Актобе, приезжий для остальных.", "Есімді және Ақтөбе үшін местный, қалғандары үшін приезжий деп шығар."], ["CASE WHEN city = 'Актобе' …", "CASE WHEN city = 'Актобе' …"],
      "SELECT name, CASE WHEN city = 'Актобе' THEN 'местный' ELSE 'приезжий' END FROM students;"),
    Q(["Сколько отличных", "Неше үздік баға"], ["Посчитай количество пятёрок с помощью SUM(CASE …).", "SUM(CASE …) арқылы бестіктер санын есепте."], ["SUM(CASE WHEN score = 5 THEN 1 ELSE 0 END)", "SUM(CASE WHEN score = 5 THEN 1 ELSE 0 END)"],
      "SELECT SUM(CASE WHEN score = 5 THEN 1 ELSE 0 END) FROM scores;", starter="SELECT * FROM scores;"),
   ]},
 ]},
 {"number": 6, "title": ["Текст и числа", "Мәтін және сандар"], "lessons": [
  {"number": 16, "title": ["Функции для текста", "Мәтін функциялары"],
   "goal": ["Научиться менять текст прямо в запросе.", "Мәтінді сұраудың ішінде өзгертуді үйрену."],
   "theory": [
    P("LENGTH(name) - длина, UPPER - большими буквами, SUBSTR(name, 1, 3) - часть текста, || - склеить строки.",
      "LENGTH(name) - ұзындық, UPPER - бас әріптермен, SUBSTR(name, 1, 3) - мәтін бөлігі, || - жолдарды біріктіру."),
    C("SELECT name, LENGTH(name) FROM students;\nSELECT name || ' из ' || city FROM students;"), TABLES,
   ],
   "tasks": [
    Q(["Длина имени", "Есім ұзындығы"], ["Выведи имя и количество букв в нём.", "Есімді және ондағы әріп санын шығар."], ["LENGTH(name)", "LENGTH(name)"], "SELECT name, LENGTH(name) FROM students;"),
    Q(["Длинные имена", "Ұзын есімдер"], ["Выведи имена длиннее 5 букв.", "5 әріптен ұзын есімдерді шығар."], ["WHERE LENGTH(name) > 5", "WHERE LENGTH(name) > 5"], "SELECT name FROM students WHERE LENGTH(name) > 5;"),
    Q(["Визитка", "Визитка"], ["Выведи строки вида: Айжан из Актобе", "Мына түрдегі жолдарды шығар: Айжан из Актобе"], ["name || ' из ' || city", "name || ' из ' || city"], "SELECT name || ' из ' || city FROM students;"),
    Q(["Инициалы класса", "Сынып нөмірі"], ["Выведи имя и только цифру класса (первый символ class).", "Есімді және сыныптың тек санын (class-тың бірінші таңбасы) шығар."], ["SUBSTR(class, 1, 1)", "SUBSTR(class, 1, 1)"], "SELECT name, SUBSTR(class, 1, 1) FROM students;"),
   ]},
  {"number": 17, "title": ["Числа и вычисления", "Сандар және есептеулер"],
   "goal": ["Научиться считать в запросах: проценты, округление, остаток.", "Сұрауларда есептеуді үйрену: пайыздар, дөңгелектеу, қалдық."],
   "theory": [
    P("В запросах можно считать: price * stock, ROUND(AVG(score), 1) - округлить до 1 знака, id % 2 - остаток.",
      "Сұрауларда есептеуге болады: price * stock, ROUND(AVG(score), 1) - 1 таңбаға дейін дөңгелектеу, id % 2 - қалдық."),
    C("SELECT name, price * stock AS total FROM products;\nSELECT ROUND(AVG(price), 1) FROM products;"), SHOP_T,
   ],
   "tasks": [
    Q(["Стоимость склада", "Қойма құны"], ["Выведи товар и стоимость его запаса (price * stock).", "Тауарды және оның қорының құнын (price * stock) шығар."], ["price * stock", "price * stock"], "SELECT name, price * stock FROM products;", starter="SELECT * FROM products;", data=DS),
    Q(["Средняя цена", "Орташа баға"], ["Выведи среднюю цену товаров, округлённую до целого.", "Тауарлардың бүтінге дейін дөңгелектенген орташа бағасын шығар."], ["ROUND(AVG(price))", "ROUND(AVG(price))"], "SELECT ROUND(AVG(price)) FROM products;", starter="SELECT * FROM products;", data=DS),
    Q(["Скидка 10%", "10% жеңілдік"], ["Выведи товар и цену со скидкой 10% (целое число).", "Тауарды және 10% жеңілдікпен бағасын (бүтін сан) шығар."], ["CAST(price * 0.9 AS INTEGER)", "CAST(price * 0.9 AS INTEGER)"], "SELECT name, CAST(price * 0.9 AS INTEGER) FROM products;", starter="SELECT * FROM products;", data=DS),
    Q(["Нет на складе", "Қоймада жоқ"], ["Выведи товары, которых нет на складе (stock = 0).", "Қоймада жоқ тауарларды (stock = 0) шығар."], ["WHERE stock = 0", "WHERE stock = 0"], "SELECT name FROM products WHERE stock = 0;", starter="SELECT * FROM products;", data=DS),
   ]},
  {"number": 18, "title": ["Проект «Рейтинг учеников»", "«Оқушылар рейтингі» жобасы"], "project": True,
   "goal": ["Составить рейтинг учеников по среднему баллу.", "Орташа балл бойынша оқушылар рейтингін құру."],
   "theory": [
    P("Соединим таблицы, посчитаем средний балл каждого и отсортируем - получится рейтинг класса.", "Кестелерді біріктіріп, әрқайсысының орташа балын есептеп, сұрыптаймыз - сынып рейтингі шығады."),
    C("SELECT students.name, ROUND(AVG(scores.score), 2) AS avg\nFROM scores JOIN students ON scores.student_id = students.id\nGROUP BY students.id\nORDER BY avg DESC, students.name;"), TABLES,
   ],
   "tasks": [
    Q(["Средний каждого", "Әрқайсысының орташасы"], ["Выведи имя и средний балл, округлённый до 2 знаков.", "Есімді және 2 таңбаға дейін дөңгелектенген орташа балды шығар."], ["ROUND(AVG(scores.score), 2) … GROUP BY students.id", "ROUND(AVG(scores.score), 2) … GROUP BY students.id"],
      "SELECT students.name, ROUND(AVG(scores.score), 2) FROM scores JOIN students ON scores.student_id = students.id GROUP BY students.id;"),
    Q(["Рейтинг", "Рейтинг"], ["Тот же запрос, но по убыванию среднего, при равенстве - по имени.", "Сол сұрау, бірақ орташаның кемуі бойынша, тең болса - есім бойынша."], ["ORDER BY 2 DESC, students.name", "ORDER BY 2 DESC, students.name"],
      "SELECT students.name, ROUND(AVG(scores.score), 2) AS avg FROM scores JOIN students ON scores.student_id = students.id GROUP BY students.id ORDER BY avg DESC, students.name;", ordered=True),
    Q(["Тройка лидеров", "Көшбасшылар үштігі"], ["Выведи только трёх лучших (имя и средний).", "Тек үш үздікті шығар (есім және орташа)."], ["… LIMIT 3", "… LIMIT 3"],
      "SELECT students.name, ROUND(AVG(scores.score), 2) AS avg FROM scores JOIN students ON scores.student_id = students.id GROUP BY students.id ORDER BY avg DESC, students.name LIMIT 3;", ordered=True),
    Q(["Лучший по информатике", "Информатикадан үздік"], ["Выведи имена всех, у кого по Информатике 5, по алфавиту.", "Информатикадан 5 алғандардың бәрінің есімін әліпби бойынша шығар."], ["JOIN … WHERE subject = 'Информатика' AND score = 5 ORDER BY name", "JOIN … WHERE subject = 'Информатика' AND score = 5 ORDER BY name"],
      "SELECT students.name FROM scores JOIN students ON scores.student_id = students.id WHERE scores.subject = 'Информатика' AND scores.score = 5 ORDER BY students.name;", ordered=True),
    Q(["Проект «Рейтинг»", "«Рейтинг» жобасы"], ["Выведи имя, город, количество оценок и средний балл (2 знака) для учеников с хотя бы двумя оценками, по убыванию среднего, при равенстве - по имени.", "Есімді, қаланы, бағалар санын және орташа балды (2 таңба) кемінде екі бағасы бар оқушылар үшін орташаның кемуі бойынша, тең болса - есім бойынша шығар."],
      ["JOIN, GROUP BY, HAVING COUNT(*) >= 2, ORDER BY", "JOIN, GROUP BY, HAVING COUNT(*) >= 2, ORDER BY"],
      "SELECT students.name, students.city, COUNT(*), ROUND(AVG(scores.score), 2) AS avg FROM scores JOIN students ON scores.student_id = students.id GROUP BY students.id HAVING COUNT(*) >= 2 ORDER BY avg DESC, students.name;", ordered=True),
   ]},
 ]},
 {"number": 7, "title": ["Связи посложнее", "Күрделірек байланыстар"], "lessons": [
  {"number": 19, "title": ["LEFT JOIN", "LEFT JOIN"],
   "goal": ["Научиться находить строки, у которых нет пары в другой таблице.", "Басқа кестеде жұбы жоқ жолдарды табуды үйрену."],
   "theory": [
    P("JOIN оставляет только строки с парой. LEFT JOIN оставляет все строки левой таблицы, а где пары нет - ставит NULL.",
      "JOIN тек жұбы бар жолдарды қалдырады. LEFT JOIN сол кестенің барлық жолын қалдырады, ал жұбы жоқ жерге NULL қояды."),
    C("SELECT students.name, scores.score\nFROM students LEFT JOIN scores ON scores.student_id = students.id;"),
    P("В этом уроке есть новенький ученик без оценок.", "Бұл сабақта бағасы жоқ жаңа оқушы бар."),
   ],
   "tasks": [
    Q(["Все и их оценки", "Барлығы және бағалары"], ["Выведи имя каждого ученика и его оценки, включая учеников без оценок.", "Әр оқушының есімі мен бағаларын, бағасы жоқтарды қоса, шығар."], ["students LEFT JOIN scores ON …", "students LEFT JOIN scores ON …"],
      "SELECT students.name, scores.score FROM students LEFT JOIN scores ON scores.student_id = students.id;", data=DN),
    Q(["Без оценок", "Бағасыздар"], ["Выведи имена учеников, у которых нет ни одной оценки.", "Бірде-бір бағасы жоқ оқушылардың есімдерін шығар."], ["LEFT JOIN … WHERE scores.student_id IS NULL", "LEFT JOIN … WHERE scores.student_id IS NULL"],
      "SELECT students.name FROM students LEFT JOIN scores ON scores.student_id = students.id WHERE scores.student_id IS NULL;", data=DN),
    Q(["Сколько оценок у каждого", "Әрқайсысында неше баға"], ["Выведи имя и количество оценок у каждого ученика (0 у тех, у кого их нет).", "Әр оқушының есімі мен бағалар санын шығар (жоқтарда 0)."], ["COUNT(scores.score) … GROUP BY students.id", "COUNT(scores.score) … GROUP BY students.id"],
      "SELECT students.name, COUNT(scores.score) FROM students LEFT JOIN scores ON scores.student_id = students.id GROUP BY students.id;", data=DN),
    Q(["Товары без заказов", "Тапсырыссыз тауарлар"], ["В базе магазина выведи товары, которые ни разу не заказывали.", "Дүкен базасында бірде-бір рет тапсырыс берілмеген тауарларды шығар."], ["products LEFT JOIN orders … IS NULL", "products LEFT JOIN orders … IS NULL"],
      "SELECT products.name FROM products LEFT JOIN orders ON orders.product_id = products.id WHERE orders.id IS NULL;", starter="SELECT * FROM products;", data=DS),
   ]},
  {"number": 20, "title": ["Подзапросы", "Ішкі сұраулар"],
   "goal": ["Научиться использовать результат одного запроса внутри другого.", "Бір сұраудың нәтижесін басқасының ішінде қолдануды үйрену."],
   "theory": [
    P("Подзапрос - запрос в скобках внутри другого. Например, ученики старше среднего возраста: WHERE age > (SELECT AVG(age) FROM students).",
      "Ішкі сұрау - басқа сұраудың ішіндегі жақшадағы сұрау. Мысалы, орташа жастан үлкен оқушылар: WHERE age > (SELECT AVG(age) FROM students)."),
    C("SELECT name FROM students WHERE age > (SELECT AVG(age) FROM students);\nSELECT name FROM students WHERE id IN (SELECT student_id FROM scores WHERE score = 5);"), TABLES,
   ],
   "tasks": [
    Q(["Старше среднего", "Орташадан үлкен"], ["Выведи имена учеников старше среднего возраста.", "Орташа жастан үлкен оқушылардың есімдерін шығар."], ["age > (SELECT AVG(age) FROM students)", "age > (SELECT AVG(age) FROM students)"], "SELECT name FROM students WHERE age > (SELECT AVG(age) FROM students);"),
    Q(["У кого есть пятёрки", "Кімде бестік бар"], ["Выведи имена учеников, у которых есть хотя бы одна пятёрка.", "Кемінде бір бестігі бар оқушылардың есімдерін шығар."], ["id IN (SELECT student_id FROM scores WHERE score = 5)", "id IN (SELECT student_id FROM scores WHERE score = 5)"],
      "SELECT name FROM students WHERE id IN (SELECT student_id FROM scores WHERE score = 5);"),
    Q(["Самый дорогой", "Ең қымбат"], ["Выведи название самого дорогого товара.", "Ең қымбат тауардың атауын шығар."], ["price = (SELECT MAX(price) FROM products)", "price = (SELECT MAX(price) FROM products)"],
      "SELECT name FROM products WHERE price = (SELECT MAX(price) FROM products);", starter="SELECT * FROM products;", data=DS),
    Q(["Без двоек и троек", "Екілік пен үштіксіз"], ["Выведи имена учеников, у которых нет оценок ниже 4 (и есть хотя бы одна оценка).", "4-тен төмен бағасы жоқ (және кемінде бір бағасы бар) оқушылардың есімдерін шығар."],
      ["id IN (SELECT student_id FROM scores) AND id NOT IN (SELECT student_id FROM scores WHERE score < 4)", "id IN (SELECT student_id FROM scores) AND id NOT IN (SELECT student_id FROM scores WHERE score < 4)"],
      "SELECT name FROM students WHERE id IN (SELECT student_id FROM scores) AND id NOT IN (SELECT student_id FROM scores WHERE score < 4);"),
   ]},
  {"number": 21, "title": ["Продажи магазина", "Дүкен сатылымы"],
   "goal": ["Применить JOIN и GROUP BY к базе магазина.", "JOIN мен GROUP BY-ды дүкен базасына қолдану."],
   "theory": [
    P("Заказы и товары связаны через product_id. Выручка заказа - qty * price.", "Тапсырыстар мен тауарлар product_id арқылы байланысқан. Тапсырыс түсімі - qty * price."),
    C("SELECT products.name, SUM(orders.qty) AS sold\nFROM orders JOIN products ON orders.product_id = products.id\nGROUP BY products.id;"), SHOP_T,
   ],
   "tasks": [
    Q(["Что заказали", "Не тапсырыс берілді"], ["Выведи день, название товара и количество для каждого заказа.", "Әр тапсырыс үшін күнді, тауар атауын және санын шығар."], ["orders JOIN products ON orders.product_id = products.id", "orders JOIN products ON orders.product_id = products.id"],
      "SELECT orders.day, products.name, orders.qty FROM orders JOIN products ON orders.product_id = products.id;", starter="SELECT * FROM orders;", data=DS),
    Q(["Продано штук", "Сатылған дана"], ["Выведи товар и сколько штук его продано всего.", "Тауарды және оның барлығы неше дана сатылғанын шығар."], ["SUM(orders.qty) … GROUP BY products.id", "SUM(orders.qty) … GROUP BY products.id"],
      "SELECT products.name, SUM(orders.qty) FROM orders JOIN products ON orders.product_id = products.id GROUP BY products.id;", starter="SELECT * FROM orders;", data=DS),
    Q(["Выручка по категориям", "Санаттар бойынша түсім"], ["Выведи категорию и выручку (сумма qty * price) по ней.", "Санатты және ол бойынша түсімді (qty * price қосындысы) шығар."], ["SUM(orders.qty * products.price) … GROUP BY products.category", "SUM(orders.qty * products.price) … GROUP BY products.category"],
      "SELECT products.category, SUM(orders.qty * products.price) FROM orders JOIN products ON orders.product_id = products.id GROUP BY products.category;", starter="SELECT * FROM orders;", data=DS),
    Q(["Лучший день", "Ең жақсы күн"], ["Выведи день с наибольшей выручкой и саму выручку.", "Түсімі ең көп күнді және түсімнің өзін шығар."], ["GROUP BY day ORDER BY 2 DESC LIMIT 1", "GROUP BY day ORDER BY 2 DESC LIMIT 1"],
      "SELECT orders.day, SUM(orders.qty * products.price) AS total FROM orders JOIN products ON orders.product_id = products.id GROUP BY orders.day ORDER BY total DESC LIMIT 1;", starter="SELECT * FROM orders;", ordered=True, data=DS),
   ]},
 ]},
 {"number": 8, "title": ["Проектируем базу", "Базаны жобалау"], "lessons": [
  {"number": 22, "title": ["CREATE TABLE подробно", "CREATE TABLE толығырақ"],
   "goal": ["Научиться создавать таблицы с ключом, типами и значениями по умолчанию.", "Кілті, түрлері және әдепкі мәндері бар кестелер жасауды үйрену."],
   "theory": [
    P("PRIMARY KEY - уникальный номер строки, NOT NULL - обязательно заполнить, DEFAULT - значение по умолчанию.",
      "PRIMARY KEY - жолдың бірегей нөмірі, NOT NULL - міндетті түрде толтыру, DEFAULT - әдепкі мән."),
    C("CREATE TABLE games (\n  id INTEGER PRIMARY KEY,\n  title TEXT NOT NULL,\n  rating INTEGER DEFAULT 5\n);\nINSERT INTO games (id, title) VALUES (1, 'Minecraft');\nSELECT * FROM games;"),
   ],
   "tasks": [
    Q(["Таблица игр", "Ойындар кестесі"], ["Создай таблицу games (id INTEGER PRIMARY KEY, title TEXT, year INTEGER) и добавь ('Minecraft', 2011) с id 1.", "games (id INTEGER PRIMARY KEY, title TEXT, year INTEGER) кестесін жасап, id 1 бар ('Minecraft', 2011) қос."],
      ["CREATE TABLE games (…); INSERT INTO games VALUES (1, 'Minecraft', 2011);", "CREATE TABLE games (…); INSERT INTO games VALUES (1, 'Minecraft', 2011);"],
      "CREATE TABLE games (id INTEGER PRIMARY KEY, title TEXT, year INTEGER);\nINSERT INTO games VALUES (1, 'Minecraft', 2011);", starter="", after="SELECT * FROM games;"),
    Q(["Значение по умолчанию", "Әдепкі мән"], ["Создай таблицу pets (name TEXT, age INTEGER DEFAULT 1) и добавь питомца Барсик, указав только имя.", "pets (name TEXT, age INTEGER DEFAULT 1) кестесін жасап, тек есімін көрсетіп, Барсик үй жануарын қос."],
      ["INSERT INTO pets (name) VALUES ('Барсик');", "INSERT INTO pets (name) VALUES ('Барсик');"],
      "CREATE TABLE pets (name TEXT, age INTEGER DEFAULT 1);\nINSERT INTO pets (name) VALUES ('Барсик');", starter="", after="SELECT name, age FROM pets;"),
    Q(["Три друга", "Үш дос"], ["Создай таблицу friends (id INTEGER PRIMARY KEY, name TEXT NOT NULL) и добавь трёх друзей: Аян, Дана, Тимур (id 1–3).", "friends (id INTEGER PRIMARY KEY, name TEXT NOT NULL) кестесін жасап, үш дос қос: Аян, Дана, Тимур (id 1–3)."],
      ["Одним INSERT с тремя скобками", "Үш жақшасы бар бір INSERT"],
      "CREATE TABLE friends (id INTEGER PRIMARY KEY, name TEXT NOT NULL);\nINSERT INTO friends VALUES (1, 'Аян'), (2, 'Дана'), (3, 'Тимур');", starter="", after="SELECT name FROM friends ORDER BY id;"),
    Q(["Связанные таблицы", "Байланысқан кестелер"], ["Создай classes (id, name) с классом (1, '6А') и kids (name, class_id) с ребёнком ('Айжан', 1). Проверка соединит их.", "classes (id, name) кестесін (1, '6А') сыныбымен және kids (name, class_id) кестесін ('Айжан', 1) баласымен жаса. Тексеру оларды біріктіреді."],
      ["Две CREATE TABLE и два INSERT", "Екі CREATE TABLE және екі INSERT"],
      "CREATE TABLE classes (id INTEGER PRIMARY KEY, name TEXT);\nCREATE TABLE kids (name TEXT, class_id INTEGER);\nINSERT INTO classes VALUES (1, '6А');\nINSERT INTO kids VALUES ('Айжан', 1);",
      starter="", after="SELECT kids.name, classes.name FROM kids JOIN classes ON kids.class_id = classes.id;"),
   ]},
  {"number": 23, "title": ["Меняем таблицу", "Кестені өзгерту"],
   "goal": ["Научиться добавлять столбцы и заполнять их.", "Бағандар қосуды және оларды толтыруды үйрену."],
   "theory": [
    P("ALTER TABLE students ADD COLUMN email TEXT; - добавить столбец. Потом его заполняют через UPDATE.",
      "ALTER TABLE students ADD COLUMN email TEXT; - баған қосу. Кейін оны UPDATE арқылы толтырады."),
    C("ALTER TABLE students ADD COLUMN email TEXT;\nUPDATE students SET email = 'aizhan@mail.ru' WHERE id = 1;"), TABLES,
   ],
   "tasks": [
    Q(["Новый столбец", "Жаңа баған"], ["Добавь в students столбец hobby TEXT и запиши ученику с id 1 хобби шахматы.", "students-ке hobby TEXT бағанын қосып, id 1 оқушыға шахматы хоббиін жаз."],
      ["ALTER TABLE … ADD COLUMN hobby TEXT; UPDATE …", "ALTER TABLE … ADD COLUMN hobby TEXT; UPDATE …"],
      "ALTER TABLE students ADD COLUMN hobby TEXT;\nUPDATE students SET hobby = 'шахматы' WHERE id = 1;", starter="", after="SELECT id, hobby FROM students WHERE hobby IS NOT NULL;"),
    Q(["Всем по умолчанию", "Бәріне әдепкі"], ["Добавь столбец active INTEGER DEFAULT 1 - у всех должна стать 1.", "active INTEGER DEFAULT 1 бағанын қос - бәрінде 1 болуы керек."], ["ADD COLUMN active INTEGER DEFAULT 1", "ADD COLUMN active INTEGER DEFAULT 1"],
      "ALTER TABLE students ADD COLUMN active INTEGER DEFAULT 1;", starter="", after="SELECT COUNT(*), MIN(active) FROM students;"),
    Q(["Посчитай и запиши", "Есепте де жаз"], ["Добавь в students столбец avg_score REAL и запиши туда средний балл каждого ученика (подзапросом).", "students-ке avg_score REAL бағанын қосып, оған әр оқушының орташа балын (ішкі сұраумен) жаз."],
      ["UPDATE students SET avg_score = (SELECT AVG(score) FROM scores WHERE student_id = students.id);", "UPDATE students SET avg_score = (SELECT AVG(score) FROM scores WHERE student_id = students.id);"],
      "ALTER TABLE students ADD COLUMN avg_score REAL;\nUPDATE students SET avg_score = (SELECT AVG(score) FROM scores WHERE scores.student_id = students.id);", starter="", after="SELECT id, ROUND(avg_score, 2) FROM students ORDER BY id;"),
    Q(["Переименуй", "Атауын өзгерт"], ["Переименуй таблицу scores в grades.", "scores кестесінің атауын grades деп өзгерт."], ["ALTER TABLE scores RENAME TO grades;", "ALTER TABLE scores RENAME TO grades;"],
      "ALTER TABLE scores RENAME TO grades;", starter="", after="SELECT COUNT(*) FROM grades;"),
   ]},
  {"number": 24, "title": ["Итоговый проект «Магазин»", "Қорытынды жоба «Дүкен»"], "project": True,
   "goal": ["Поработать с базой магазина как настоящий аналитик и защитить отчёт.", "Дүкен базасымен нағыз талдаушы сияқты жұмыс істеп, есепті қорғау."],
   "theory": [
    P("Финальный проект - отчёт для владельца магазина: что продаётся, что закончилось, сколько заработали. На защите объясни каждый запрос.",
      "Қорытынды жоба - дүкен иесіне арналған есеп: не сатылады, не таусылды, қанша тапты. Қорғауда әр сұрауды түсіндір."), SHOP_T,
   ],
   "tasks": [
    Q(["Каталог", "Каталог"], ["Выведи название, категорию и цену всех товаров по категории, внутри - по цене.", "Барлық тауардың атауын, санатын және бағасын санат бойынша, ішінде - баға бойынша шығар."], ["ORDER BY category, price", "ORDER BY category, price"],
      "SELECT name, category, price FROM products ORDER BY category, price;", starter="SELECT * FROM products;", ordered=True, data=DS),
    Q(["Заканчиваются", "Таусылып жатыр"], ["Выведи товары, которых на складе меньше 10, и пометку: нет, если 0, иначе мало.", "Қоймада 10-нан аз тауарларды және белгіні шығар: 0 болса нет, әйтпесе мало."], ["WHERE stock < 10 и CASE", "WHERE stock < 10 және CASE"],
      "SELECT name, CASE WHEN stock = 0 THEN 'нет' ELSE 'мало' END FROM products WHERE stock < 10;", starter="SELECT * FROM products;", data=DS),
    Q(["Общая выручка", "Жалпы түсім"], ["Выведи общую выручку магазина.", "Дүкеннің жалпы түсімін шығар."], ["SUM(qty * price) с JOIN", "JOIN-мен SUM(qty * price)"],
      "SELECT SUM(orders.qty * products.price) FROM orders JOIN products ON orders.product_id = products.id;", starter="SELECT * FROM orders;", data=DS),
    Q(["Новый товар", "Жаңа тауар"], ["Добавь товар (100, 'Глобус', 'Канцелярия', 3500, 7).", "(100, 'Глобус', 'Канцелярия', 3500, 7) тауарын қос."], ["INSERT INTO products VALUES (…);", "INSERT INTO products VALUES (…);"],
      "INSERT INTO products VALUES (100, 'Глобус', 'Канцелярия', 3500, 7);", starter="", after="SELECT name, price FROM products WHERE id = 100;", data=DS),
    Q(["Отчёт", "Есеп"], ["Итоговый отчёт: для каждой категории - количество товаров, сколько штук продано (0, если не продавали) и выручка (0, если нет), по убыванию выручки, при равенстве - по категории.", "Қорытынды есеп: әр санат үшін - тауарлар саны, неше дана сатылғаны (сатылмаса 0) және түсім (жоқ болса 0), түсімнің кемуі бойынша, тең болса - санат бойынша."],
      ["LEFT JOIN, COALESCE, GROUP BY, ORDER BY", "LEFT JOIN, COALESCE, GROUP BY, ORDER BY"],
      "SELECT products.category, COUNT(DISTINCT products.id), COALESCE(SUM(orders.qty), 0), COALESCE(SUM(orders.qty * products.price), 0) AS income FROM products LEFT JOIN orders ON orders.product_id = products.id GROUP BY products.category ORDER BY income DESC, products.category;",
      starter="SELECT * FROM products;", ordered=True, data=DS),
   ]},
 ]},
]
