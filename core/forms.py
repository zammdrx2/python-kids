from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .ui import texts_for


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    role = forms.ChoiceField(choices=[("student", ""), ("teacher", "")], initial="student", required=False,
                             widget=forms.RadioSelect)
    class_code = forms.CharField(max_length=8, required=False)
    field_order = ("first_name", "last_name", "username", "password1", "password2", "role", "class_code")

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username")

    def __init__(self, *args, lang="ru", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        t = texts_for(lang)
        labels = {"first_name": t["first_name"], "last_name": t["last_name"], "username": t["username"],
                  "password1": t["password"], "password2": t["password2"], "role": t["role"],
                  "class_code": t["class_code"]}
        self.fields["role"].choices = [("student", t["role_student"]), ("teacher", t["role_teacher"])]
        for name, label in labels.items():
            self.fields[name].label = label
            self.fields[name].help_text = ""
        self.fields["class_code"].help_text = t["class_code_help"]

    def clean_class_code(self):
        from course.models import Classroom
        code = (self.cleaned_data.get("class_code") or "").strip().upper()
        if code and not Classroom.objects.filter(code=code).exists():
            raise forms.ValidationError(texts_for(self.lang)["class_not_found"])
        return code


class LocalizedLoginForm(AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        lang = request.session.get("lang", "ru") if request else "ru"
        t = texts_for(lang)
        self.fields["username"].label = t["username"]
        self.fields["password"].label = t["password"]
