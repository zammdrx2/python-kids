from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("progress/", views.group_progress, name="course_progress"),
    path("task/<int:task_id>/submit/", views.submit, name="course_submit"),
    path("lesson/<int:number>/", views.legacy_lesson),
    path("module/<int:number>/", views.legacy_module),
    path("<slug:course>/", views.course_home, name="course_home"),
    path("<slug:course>/module/<int:number>/", views.module_detail, name="course_module"),
    path("<slug:course>/lesson/<int:number>/", views.lesson_detail, name="course_lesson"),
]
