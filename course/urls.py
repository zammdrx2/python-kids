from django.urls import path

from . import views

urlpatterns = [
    path("", views.course_home, name="course_home"),
    path("lesson/<int:number>/", views.lesson_detail, name="course_lesson"),
    path("task/<int:task_id>/submit/", views.submit, name="course_submit"),
    path("progress/", views.group_progress, name="course_progress"),
]
