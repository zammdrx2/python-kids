"""
Курсы программирования для детей: курс → модули → уроки → задания, решения учеников.

Код учеников выполняется в браузере (Python — через Pyodide, HTML/CSS — в окне
предпросмотра), сервер хранит задания, проверки и результаты. Тексты — ru / kk.
"""
from django.conf import settings
from django.db import models

from core.ui import tr


class Course(models.Model):
    class Kind(models.TextChoices):
        PYTHON = "python", "Python"
        WEB = "web", "HTML и CSS"
        JS = "js", "JavaScript"
        SQL = "sql", "SQL"
        WORD = "word", "Word"
        EXCEL = "excel", "Excel"
        PPTX = "pptx", "PowerPoint"

    slug = models.SlugField("Адрес", unique=True)
    kind = models.CharField("Тип", max_length=10, choices=Kind.choices, default=Kind.PYTHON)
    title_ru = models.CharField("Название (рус)", max_length=200)
    title_kk = models.CharField("Атауы (қаз)", max_length=200, blank=True)
    desc_ru = models.CharField("Описание (рус)", max_length=300, blank=True)
    desc_kk = models.CharField("Сипаттама (қаз)", max_length=300, blank=True)
    color = models.CharField("Цвет", max_length=20, default="#FFD166")
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"

    def __str__(self):
        return self.title_ru

    def title(self, lang):
        return tr(self, "title", lang)

    def desc(self, lang):
        return tr(self, "desc", lang)


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules", verbose_name="Курс")
    number = models.PositiveIntegerField("Номер")
    title_ru = models.CharField("Название (рус)", max_length=200)
    title_kk = models.CharField("Атауы (қаз)", max_length=200, blank=True)

    class Meta:
        ordering = ["course", "number"]
        unique_together = ("course", "number")
        verbose_name = "Модуль"
        verbose_name_plural = "Модули"

    def __str__(self):
        return f"{self.number}. {self.title_ru}"

    def title(self, lang):
        return tr(self, "title", lang)


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons", verbose_name="Курс")
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    number = models.PositiveIntegerField("Номер урока")
    title_ru = models.CharField("Тема (рус)", max_length=200)
    title_kk = models.CharField("Тақырып (қаз)", max_length=200, blank=True)
    goal_ru = models.CharField("Цель (рус)", max_length=300, blank=True)
    goal_kk = models.CharField("Мақсат (қаз)", max_length=300, blank=True)
    # Теория — список блоков: {"p": [ru, kk]} абзац или {"code": "..."} пример кода
    theory = models.JSONField("Теория", default=list, blank=True)
    is_project = models.BooleanField("Урок-проект", default=False)

    class Meta:
        ordering = ["course", "number"]
        unique_together = ("course", "number")
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"

    def __str__(self):
        return f"Урок {self.number}. {self.title_ru}"

    def title(self, lang):
        return tr(self, "title", lang)

    def goal(self, lang):
        return tr(self, "goal", lang)

    def theory_blocks(self, lang):
        blocks = []
        for b in self.theory:
            if "code" in b:
                blocks.append({"code": b["code"]})
            else:
                ru, kk = b["p"]
                blocks.append({"p": kk if lang == "kk" and kk else ru})
        return blocks


class Task(models.Model):
    class Kind(models.TextChoices):
        TESTED = "tested", "С автопроверкой"
        PROJECT = "project", "Свободный проект"
        WEB = "web", "HTML/CSS с проверкой страницы"
        JS = "js", "JavaScript с тестами"
        SQL = "sql", "SQL-запрос с проверкой результата"
        QUIZ = "quiz", "Тест с вариантами ответа"
        FILE = "file", "Файл Word/Excel/PowerPoint с проверкой"

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="tasks")
    order = models.PositiveIntegerField("Порядок", default=1)
    kind = models.CharField("Тип", max_length=10, choices=Kind.choices, default=Kind.TESTED)
    title_ru = models.CharField("Название (рус)", max_length=200)
    title_kk = models.CharField("Атауы (қаз)", max_length=200, blank=True)
    text_ru = models.TextField("Условие (рус)")
    text_kk = models.TextField("Шарты (қаз)", blank=True)
    hint_ru = models.TextField("Подсказка (рус)", blank=True)
    hint_kk = models.TextField("Кеңес (қаз)", blank=True)
    starter_code = models.TextField("Начальный код", blank=True)
    # Тесты: [{"input": "строка1\nстрока2", "output": "ожидаемый вывод"}]
    tests = models.JSONField("Тесты", default=list, blank=True)
    solution = models.TextField("Эталонное решение (видит только преподаватель)", blank=True)
    points = models.PositiveIntegerField("Баллы", default=10)

    class Meta:
        ordering = ["lesson", "order"]
        unique_together = ("lesson", "order")
        verbose_name = "Задание"
        verbose_name_plural = "Задания"

    def __str__(self):
        return f"{self.lesson.number}.{self.order} {self.title_ru}"

    def title(self, lang):
        return tr(self, "title", lang)

    def text(self, lang):
        return tr(self, "text", lang)

    def hint(self, lang):
        return tr(self, "hint", lang)


class Submission(models.Model):
    """Последнее и лучшее решение ученика по заданию (одна запись на пару ученик–задание)."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="course_submissions")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="submissions")
    code = models.TextField(blank=True)
    passed_tests = models.PositiveIntegerField(default=0)
    total_tests = models.PositiveIntegerField(default=0)
    solved = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    solved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "task")
        verbose_name = "Решение"
        verbose_name_plural = "Решения"

    def __str__(self):
        return f"{self.user} — {self.task} — {'✓' if self.solved else '…'}"
