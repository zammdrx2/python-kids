from django.contrib import admin
from django.templatetags.static import static
from django.urls import include, path
from django.views.generic import RedirectView

admin.site.site_header = "stack. - панель преподавателя"
admin.site.site_title = "stack."

urlpatterns = [
    path("admin/", admin.site.urls),
    # браузеры сами запрашивают /favicon.ico - отдаём значок сайта
    path("favicon.ico", RedirectView.as_view(url=static("img/favicon.ico"), permanent=True)),
    path("", include("core.urls")),
    path("", include("course.urls")),
]
