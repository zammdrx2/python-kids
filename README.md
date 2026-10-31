# Python для детей

Сайт с курсами программирования для детей 11–15 лет на русском и казахском языках. Ученик читает короткую теорию, пишет код прямо в браузере и сразу получает автопроверку.

- **Python** — 24 урока (6 модулей, 3 месяца по 2 урока в неделю), 144 задания; код выполняется через Pyodide.
- **HTML и CSS** — 24 урока (6 модулей), 120 заданий; страница ученика видна рядом с кодом, проверка смотрит теги, текст, атрибуты и стили.

- **JavaScript** — 24 урока, 102 задания; код выполняется в Web Worker, проверка сравнивает вывод `console.log`.
- **SQL** — 24 урока, 99 заданий; настоящая база SQLite в браузере (sql.js), ответ сравнивается с правильной таблицей на двух наборах данных.

Уроки открываются по порядку: следующий доступен, когда решены все задания предыдущего.

![Django](https://img.shields.io/badge/Django-5-0C4B33) ![Pyodide](https://img.shields.io/badge/Pyodide-0.26-blue) ![tests](https://img.shields.io/badge/tests-passing-brightgreen)

## Возможности

- **24 урока**: print и арифметика → переменные и input → if/elif → циклы → строки → списки → функции и словари.
- **Автопроверка**: код ученика запускается на тестах, при ошибке видно, что ожидалось и что получилось.
- **Код выполняется в браузере** (Pyodide в Web Worker): сервер не нагружается, бесконечный цикл останавливается через 5 секунд.
- **Подсказки для детей**: ошибки Python объясняются простыми словами на русском и казахском.
- **6 проектов**: «Анкета», «Викторина», «Угадай число», «Шифровальщик», «Журнал оценок», игра «Камень, ножницы, бумага».
- **Для преподавателя**: таблица прогресса группы (`/progress/`) и код каждого решения в админке.

## Как устроено

| Часть | Что делает |
|---|---|
| `course/models.py` | Модули, уроки, задания с тестами, решения учеников |
| `course/services.py` | Приём результатов, баллы, прогресс ученика и группы |
| `static/js/course.js` | Редактор, запуск и проверка кода, отправка результата |
| `static/js/pyworker.js` | Web Worker: выполняет Python через Pyodide |
| `course/data/build/` | Тексты уроков и заданий; `build.py` проверяет эталонные решения |
| `core/` | Вход, регистрация, переключение языка RU / ҚАЗ |

## Запуск

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py load_course      # загрузить 24 урока
python manage.py createsuperuser  # аккаунт преподавателя
python manage.py runserver
```

Сайт откроется на http://127.0.0.1:8000.

Тесты: `python manage.py test`. Через Docker: `docker compose up --build`.

## Как менять уроки

Курс HTML и CSS лежит в `course/data/build/web_course.py`: `python course/data/build/web_course.py` пишет `course/data/web.json`, а `node course/data/build/check_web.js` проверяет в браузере, что эталоны проходят проверки, а начальный код — нет.

Курсы JavaScript и SQL: `python course/data/build/js_course.py` и `python course/data/build/sql_course.py` (ожидаемые ответы вычисляются из эталонов), `node course/data/build/check_sql.js` сверяет ответы с движком сайта.

Курс Python:

Тексты уроков и задания лежат в `course/data/build/part1.py` (уроки 1–12) и `part2.py` (уроки 13–24). После правок:

```bash
python course/data/build/build.py   # проверит, что все эталоны проходят тесты, и запишет course.json
python manage.py load_course        # обновит уроки, решения учеников сохранятся
```

## Хостинг

Скрипт `deploy/pythonanywhere_setup.sh` настраивает сайт на PythonAnywhere: окружение, `.env`, базу, уроки, статику и WSGI-файл.
