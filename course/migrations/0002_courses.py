# Несколько курсов: модель Course, курс у модулей и уроков.
# Существующие модули, уроки и решения учеников переходят в курс «python».
import django.db.models.deletion
from django.db import migrations, models


def assign_python(apps, schema_editor):
    Course = apps.get_model("course", "Course")
    Module = apps.get_model("course", "Module")
    Lesson = apps.get_model("course", "Lesson")
    if not Module.objects.exists():
        return
    python, _ = Course.objects.get_or_create(slug="python", defaults={
        "kind": "python", "title_ru": "Python", "title_kk": "Python", "color": "#FFD166", "order": 1,
    })
    Module.objects.filter(course__isnull=True).update(course=python)
    Lesson.objects.filter(course__isnull=True).update(course=python)


class Migration(migrations.Migration):

    dependencies = [
        ("course", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Course",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(unique=True, verbose_name="Адрес")),
                ("kind", models.CharField(choices=[("python", "Python"), ("web", "HTML и CSS")], default="python", max_length=10, verbose_name="Тип")),
                ("title_ru", models.CharField(max_length=200, verbose_name="Название (рус)")),
                ("title_kk", models.CharField(blank=True, max_length=200, verbose_name="Атауы (қаз)")),
                ("desc_ru", models.CharField(blank=True, max_length=300, verbose_name="Описание (рус)")),
                ("desc_kk", models.CharField(blank=True, max_length=300, verbose_name="Сипаттама (қаз)")),
                ("color", models.CharField(default="#FFD166", max_length=20, verbose_name="Цвет")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
            ],
            options={"verbose_name": "Курс", "verbose_name_plural": "Курсы", "ordering": ["order", "id"]},
        ),
        migrations.AlterField(model_name="module", name="number", field=models.PositiveIntegerField(verbose_name="Номер")),
        migrations.AlterField(model_name="lesson", name="number", field=models.PositiveIntegerField(verbose_name="Номер урока")),
        migrations.AddField(
            model_name="module", name="course",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name="modules", to="course.course", verbose_name="Курс"),
        ),
        migrations.AddField(
            model_name="lesson", name="course",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name="lessons", to="course.course", verbose_name="Курс"),
        ),
        migrations.RunPython(assign_python, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="module", name="course",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="modules", to="course.course", verbose_name="Курс"),
        ),
        migrations.AlterField(
            model_name="lesson", name="course",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lessons", to="course.course", verbose_name="Курс"),
        ),
        migrations.AlterModelOptions(name="module", options={"ordering": ["course", "number"], "verbose_name": "Модуль", "verbose_name_plural": "Модули"}),
        migrations.AlterModelOptions(name="lesson", options={"ordering": ["course", "number"], "verbose_name": "Урок", "verbose_name_plural": "Уроки"}),
        migrations.AlterUniqueTogether(name="module", unique_together={("course", "number")}),
        migrations.AlterUniqueTogether(name="lesson", unique_together={("course", "number")}),
        migrations.AlterField(
            model_name="task", name="kind",
            field=models.CharField(choices=[("tested", "С автопроверкой"), ("project", "Свободный проект"), ("web", "HTML/CSS с проверкой страницы")], default="tested", max_length=10, verbose_name="Тип"),
        ),
    ]
