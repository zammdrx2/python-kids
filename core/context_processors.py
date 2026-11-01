from .ui import get_lang, texts_for


def ui(request):
    """Добавляет в каждый шаблон текущий язык и словарь текстов интерфейса (t)."""
    lang = get_lang(request)
    teacher = False
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        teacher = user.is_staff or user.groups.filter(name="Учителя").exists()
    return {"lang": lang, "t": texts_for(lang), "is_teacher": teacher}
