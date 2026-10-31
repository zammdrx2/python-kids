"""
Общие тексты интерфейса на русском и казахском.
Язык хранится в сессии пользователя (ключ "lang").
"""
DEFAULT_LANG = "ru"
SUPPORTED = ("ru", "kk")

TEXTS = {
    "site_title": {"ru": "Python для детей", "kk": "Балаларға арналған Python"},
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
    "admin": {"ru": "Панель преподавателя", "kk": "Мұғалім панелі"},
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
