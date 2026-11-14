from pathlib import Path

from django.conf import settings

from .ui import get_lang, texts_for


def _asset_version():
    """Метка версии CSS/JS: меняется при каждом обновлении файлов, и браузер берёт свежие, а не из кэша."""
    files = [Path(settings.BASE_DIR) / "static" / "css" / "style.css", Path(settings.BASE_DIR) / "static" / "js" / "course.js"]
    return str(int(max(f.stat().st_mtime for f in files if f.exists()) if any(f.exists() for f in files) else 0))


ASSET_VERSION = _asset_version()


def ui(request):
    """Добавляет в каждый шаблон текущий язык и словарь текстов интерфейса (t)."""
    lang = get_lang(request)
    teacher = False
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        teacher = user.is_staff or user.groups.filter(name="Учителя").exists()
    streak_days = 0
    if user is not None and user.is_authenticated:
        from course.services import streak
        streak_days = streak(user)["days"]
    return {"lang": lang, "t": texts_for(lang), "is_teacher": teacher, "v": ASSET_VERSION, "streak_days": streak_days}
