from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Python для детей — панель преподавателя"
admin.site.site_title = "Python для детей"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("", include("course.urls")),
]
