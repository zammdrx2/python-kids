"""
Настройки проекта «stack.» (детская IT-школа) - курс программирования с автопроверкой.

Секреты и параметры окружения читаются из переменных окружения
(файл .env подгружается автоматически, см. _load_env ниже).
Если переменная POSTGRES_DB не задана, используется SQLite -
так проект запускается на любом компьютере без установки базы данных.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_env(path: Path = BASE_DIR / ".env") -> None:
    """Подгружает переменные из файла .env (если он есть) в окружение."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_env()

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "dev-only-insecure-key-change-me",  # только для локальной разработки
)
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [h for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h]
# Для доступа по https через туннель или хостинг, например https://*.trycloudflare.com
CSRF_TRUSTED_ORIGINS = [o for o in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "course",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # раздача CSS/JS без отдельного веб-сервера
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.ui",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

if os.getenv("POSTGRES_DB"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["POSTGRES_DB"],
            "USER": os.getenv("POSTGRES_USER", "postgres"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
            "HOST": os.getenv("POSTGRES_HOST", "localhost"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 6}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

LANGUAGE_CODE = "ru"
TIME_ZONE = "Asia/Aqtobe"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
# WhiteNoise отдаёт CSS и при DEBUG=0 без отдельного collectstatic
WHITENOISE_USE_FINDERS = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"

# Количество вопросов в одном тесте
QUESTIONS_PER_TOPIC_TEST = 10
QUESTIONS_PER_MIXED_TEST = 20

# Pyodide (Python в браузере) для курса. Можно указать свою копию через переменную окружения.
PYODIDE_URL = os.getenv("PYODIDE_URL", "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/")

# Не обрывать длинные POST-запросы при завершении ЕНТ (120 заданий)

# Хостинг (PythonAnywhere) принимает https и передаёт запрос дальше - так ссылки в превью будут https
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Платный доступ: первые FREE_LESSONS уроков каждого курса бесплатны, дальше - подписка.
# Оплату ученик делает в Kaspi (самозанятый), администратор отмечает её на странице /payments/.
PRICE_MONTH = int(os.getenv("PRICE_MONTH", "14990"))
# цена для учеников классов администратора (тех, кто вступил по коду класса учителя-администратора)
CLASS_PRICE = int(os.getenv("CLASS_PRICE", "7990"))
FREE_LESSONS = int(os.getenv("FREE_LESSONS", "2"))
KASPI_PAY_URL = os.getenv("KASPI_PAY_URL", "https://qr.kaspi.kz/19137848668473225954748785273418335341873")
PAY_WHATSAPP = os.getenv("PAY_WHATSAPP", "77078286375")
