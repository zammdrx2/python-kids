from django.contrib import admin

from .models import Course, Lesson, Module, Submission, Task


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ("number", "title_ru", "is_project")
    show_change_link = True


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title_ru", "slug", "kind", "order")


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("number", "title_ru", "title_kk", "course")
    list_filter = ("course",)
    inlines = [LessonInline]


class TaskInline(admin.StackedInline):
    model = Task
    extra = 0
    fields = ("order", "kind", "title_ru", "title_kk", "text_ru", "text_kk", "hint_ru", "hint_kk",
              "starter_code", "tests", "solution", "points")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("number", "title_ru", "course", "module", "is_project")
    list_filter = ("course", "module", "is_project")
    inlines = [TaskInline]


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    """Преподаватель видит код каждого решения."""
    list_display = ("user", "task", "solved", "passed_tests", "total_tests", "attempts", "updated_at")
    list_filter = ("solved", "task__lesson__course", "task__lesson")
    search_fields = ("user__username", "user__last_name")
    readonly_fields = ("user", "task", "code", "passed_tests", "total_tests", "solved", "attempts", "updated_at", "solved_at")
