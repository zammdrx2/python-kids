from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("course", "0002_courses"),
    ]

    operations = [
        migrations.AlterField(
            model_name="course", name="kind",
            field=models.CharField(choices=[("python", "Python"), ("web", "HTML и CSS"), ("js", "JavaScript"), ("sql", "SQL")], default="python", max_length=10, verbose_name="Тип"),
        ),
        migrations.AlterField(
            model_name="task", name="kind",
            field=models.CharField(choices=[("tested", "С автопроверкой"), ("project", "Свободный проект"), ("web", "HTML/CSS с проверкой страницы"), ("js", "JavaScript с тестами"), ("sql", "SQL-запрос с проверкой результата")], default="tested", max_length=10, verbose_name="Тип"),
        ),
    ]
