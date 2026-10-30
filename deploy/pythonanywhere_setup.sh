#!/bin/bash
# Настройка сайта «Python для детей» на PythonAnywhere.
# Запуск в Bash-консоли PythonAnywhere (из домашней папки):
#   git clone https://github.com/<логин>/python-kids.git
#   bash python-kids/deploy/pythonanywhere_setup.sh
# Повторный запуск безопасен: обновит зависимости, базу, статику и WSGI-файл.

set -e
cd "$(dirname "$0")/.."
PROJECT_DIR="$(pwd)"
USER_NAME="$(whoami)"
DOMAIN="${USER_NAME}.pythonanywhere.com"

# 1. Подходящая версия Python
for v in 3.13 3.12 3.11 3.10; do
  if command -v "python$v" >/dev/null 2>&1; then PY="python$v"; PYV="$v"; break; fi
done
[ -z "$PY" ] && { echo "Не найден Python 3.10+"; exit 1; }
echo "Python: $PY"

# 2. Виртуальное окружение и зависимости
[ -d venv ] || "$PY" -m venv venv
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet "Django>=5.0,<6.0" "whitenoise>=6.6"

# 3. Настройки (.env создаётся один раз, секретный ключ генерируется автоматически)
if [ ! -f .env ]; then
  SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
  {
    echo "DJANGO_DEBUG=0"
    echo "DJANGO_SECRET_KEY=$SECRET"
    echo "DJANGO_ALLOWED_HOSTS=$DOMAIN"
    echo "DJANGO_CSRF_TRUSTED_ORIGINS=https://$DOMAIN"
  } > .env
  echo ".env создан для $DOMAIN"
fi

# 4. База данных, уроки курса, статические файлы
python manage.py migrate --noinput
python manage.py load_course
python manage.py collectstatic --noinput >/dev/null

# 5. WSGI-файл веб-приложения (появляется после создания приложения на вкладке Web)
WSGI_FILE="/var/www/${USER_NAME}_pythonanywhere_com_wsgi.py"
WSGI_DONE=""
if [ -f "$WSGI_FILE" ]; then
  {
    echo "import os"
    echo "import sys"
    echo ""
    echo "path = \"$PROJECT_DIR\""
    echo "if path not in sys.path:"
    echo "    sys.path.insert(0, path)"
    echo "os.environ[\"DJANGO_SETTINGS_MODULE\"] = \"config.settings\""
    echo ""
    echo "from django.core.wsgi import get_wsgi_application"
    echo "application = get_wsgi_application()"
  } > "$WSGI_FILE"
  echo "WSGI-файл настроен: $WSGI_FILE"
  WSGI_DONE=1
fi

echo ""
echo "================= ГОТОВО ================="
echo "Настройки для вкладки Web на PythonAnywhere:"
echo "  Python version:  $PYV"
echo "  Source code:     $PROJECT_DIR"
echo "  Virtualenv:      $PROJECT_DIR/venv"
echo "  Static files:    URL /static/   Directory $PROJECT_DIR/staticfiles"
if [ -z "$WSGI_DONE" ]; then
  echo ""
  echo "Веб-приложение ещё не создано. Создайте его на вкладке Web (Manual configuration, Python $PYV),"
  echo "затем запустите этот скрипт ещё раз — он сам настроит WSGI-файл."
fi
echo ""
echo "Аккаунт преподавателя:  source venv/bin/activate && python manage.py createsuperuser"
echo "После настройки нажмите зелёную кнопку Reload на вкладке Web."
echo "Адрес сайта: https://$DOMAIN"
