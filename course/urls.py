from django.urls import path

from . import classroom_views as cv
from . import pay_views as pv
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("progress/", views.group_progress, name="course_progress"),
    path("task/<int:task_id>/submit/", views.submit, name="course_submit"),
    path("lesson/<int:number>/", views.legacy_lesson),
    path("module/<int:number>/", views.legacy_module),
    path("teacher/", cv.teacher_home, name="teacher_home"),
    path("teacher/class/<int:pk>/", cv.teacher_class, name="teacher_class"),
    path("teacher/class/<int:pk>/delete/", cv.teacher_delete_class, name="teacher_delete_class"),
    path("teacher/class/<int:pk>/student/<int:user_id>/", cv.teacher_student, name="teacher_student"),
    path("teacher/class/<int:pk>/student/<int:user_id>/remove/", cv.teacher_remove_student, name="teacher_remove_student"),
    path("pay/", pv.pay, name="pay"),
    path("payments/", pv.payments, name="payments"),
    path("payments/<int:user_id>/add/", pv.payment_add, name="payment_add"),
    path("join/", cv.join_class, name="join_class"),
    path("join/<str:code>/", cv.join_class, name="join_class_code"),
    path("certificate/<str:code>/", cv.certificate_verify, name="certificate_verify"),
    path("<slug:course>/certificate/", cv.certificate, name="certificate"),
    path("<slug:course>/", views.course_home, name="course_home"),
    path("<slug:course>/module/<int:number>/", views.module_detail, name="course_module"),
    path("<slug:course>/module/<int:number>/test/", views.module_test, name="course_module_test"),
    path("<slug:course>/lesson/<int:number>/", views.lesson_detail, name="course_lesson"),
]
