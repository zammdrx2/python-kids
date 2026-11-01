from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LocalizedLoginForm

urlpatterns = [
    path("lang/", views.set_language, name="set_language"),
    path("robots.txt", views.robots_txt, name="robots"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap"),
    path("signup/", views.signup, name="signup"),
    path("login/", auth_views.LoginView.as_view(authentication_form=LocalizedLoginForm), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
