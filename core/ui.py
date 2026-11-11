"""
Общие тексты интерфейса на русском и казахском.
Язык хранится в сессии пользователя (ключ "lang").
"""
DEFAULT_LANG = "ru"
SUPPORTED = ("ru", "kk")

TEXTS = {
    "site_title": {"ru": "pythonkids", "kk": "pythonkids"},
    "brand": {"ru": "Python для детей", "kk": "Балаларға Python"},
    "login": {"ru": "Войти", "kk": "Кіру"},
    "logout": {"ru": "Выйти", "kk": "Шығу"},
    "signup": {"ru": "Регистрация", "kk": "Тіркелу"},
    "username": {"ru": "Логин", "kk": "Логин"},
    "password": {"ru": "Пароль", "kk": "Құпиясөз"},
    "password2": {"ru": "Повторите пароль", "kk": "Құпиясөзді қайталаңыз"},
    "first_name": {"ru": "Имя", "kk": "Аты"},
    "last_name": {"ru": "Фамилия", "kk": "Тегі"},
    "no_account": {"ru": "Нет аккаунта?", "kk": "Аккаунт жоқ па?"},
    "have_account": {"ru": "Уже есть аккаунт?", "kk": "Аккаунт бар ма?"},
    "lessons": {"ru": "Уроки", "kk": "Сабақтар"},
    "group": {"ru": "Прогресс группы", "kk": "Топ үлгерімі"},
    "skip": {"ru": "Перейти к содержимому", "kk": "Мазмұнға өту"},
    "meta_title": {"ru": "Программирование для детей - Python, HTML, Word, Excel | pythonkids", "kk": "Балаларға бағдарламалау - Python, HTML, Word, Excel | pythonkids"},
    "meta_description": {"ru": "Бесплатные курсы для детей 10–15 лет на русском и казахском: Python, HTML и CSS, JavaScript, SQL, Word, Excel и PowerPoint. Код пишется в браузере, задания проверяются автоматически, за курс - сертификат.", "kk": "10–15 жастағы балаларға қазақ және орыс тілдерінде тегін курстар: Python, HTML және CSS, JavaScript, SQL, Word, Excel және PowerPoint. Код браузерде жазылады, тапсырмалар автоматты тексеріледі, курс үшін - сертификат."},
    "meta_og_description": {"ru": "Python, HTML, JavaScript, SQL, Word, Excel и PowerPoint: пиши код в браузере, задания проверяются сразу.", "kk": "Python, HTML, JavaScript, SQL, Word, Excel және PowerPoint: кодты браузерде жаз, тапсырмалар бірден тексеріледі."},
    "admin": {"ru": "Админка", "kk": "Әкімші панелі"},
    "payments": {"ru": "Оплаты", "kk": "Төлемдер"},
    "access": {"ru": "Доступ", "kk": "Қолжетімділік"},
    "teacher_cabinet": {"ru": "Кабинет учителя", "kk": "Мұғалім кабинеті"},
    "my_class": {"ru": "Мой класс", "kk": "Менің сыныбым"},
    "role": {"ru": "Кто ты?", "kk": "Сен кімсің?"},
    "role_student": {"ru": "Я ученик", "kk": "Мен оқушымын"},
    "role_teacher": {"ru": "Я учитель", "kk": "Мен мұғаліммін"},
    "class_code": {"ru": "Код класса (если дал учитель)", "kk": "Сынып коды (мұғалім берсе)"},
    "class_code_help": {"ru": "Можно оставить пустым и вступить в класс позже.", "kk": "Бос қалдырып, сыныпқа кейін қосылуға болады."},
    "class_not_found": {"ru": "Класс с таким кодом не найден. Проверь код у учителя.", "kk": "Мұндай кодты сынып табылмады. Кодты мұғалімнен тексер."},
}


def get_lang(request) -> str:
    lang = request.session.get("lang", DEFAULT_LANG)
    return lang if lang in SUPPORTED else DEFAULT_LANG


def texts_for(lang: str) -> dict:
    return {key: value.get(lang) or value["ru"] for key, value in TEXTS.items()}


def tr(obj, field: str, lang: str) -> str:
    """Текст поля на выбранном языке с запасным вариантом на русском."""
    value = getattr(obj, f"{field}_{lang}", "") or ""
    return value or getattr(obj, f"{field}_ru", "")
