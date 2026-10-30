from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import SignUpForm
from .ui import SUPPORTED, get_lang


@require_POST
def set_language(request):
    lang = request.POST.get("lang")
    if lang in SUPPORTED:
        request.session["lang"] = lang
    next_url = request.POST.get("next", "/")
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = "/"
    return redirect(next_url)


def signup(request):
    lang = get_lang(request)
    form = SignUpForm(request.POST or None, lang=lang)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("course_home")
    return render(request, "registration/signup.html", {"form": form})
