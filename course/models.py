"""
Курсы программирования для детей: курс → модули → уроки → задания, решения учеников.

Код учеников выполняется в браузере (Python - через Pyodide, HTML/CSS - в окне
предпросмотра), сервер хранит задания, проверки и результаты. Тексты - ru / kk.
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
    # Итоговый тест модуля: [{"q": [ru, kk], "code": "...", "options": [...], "answer": i}]
    test = models.JSONField("Итоговый тест", default=list, blank=True)

    class Meta:
        ordering = ["course", "number"]
        unique_together = ("course", "number")
        verbose_name = "Модуль"
        verbose_name_plural = "Модули"

    def __str__(self):
        return f"{self.number}. {self.title_ru}"

    def title(self, lang):
        return tr(self, "title", lang)

    @property
    def pass_score(self):
        """Сколько верных ответов нужно, чтобы сдать тест: 90% (18 из 20)."""
        import math
        return math.ceil(len(self.test) * 0.9)


class ModuleTestResult(models.Model):
    """Результат ученика по итоговому тесту модуля (одна запись на пару ученик–модуль)."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="module_tests",
                             verbose_name="Ученик")
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="results", verbose_name="Модуль")
    best = models.PositiveIntegerField("Лучший результат", default=0)
    last = models.PositiveIntegerField("Последняя попытка", default=0)
    total = models.PositiveIntegerField("Вопросов", default=0)
    passed = models.BooleanField("Сдан", default=False)
    attempts = models.PositiveIntegerField("Попыток", default=0)
    passed_at = models.DateTimeField("Сдан", null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "module")
        verbose_name = "Тест модуля"
        verbose_name_plural = "Тесты модулей"

    def __str__(self):
        return f"{self.user} - {self.module}: {self.best}/{self.total}"


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons", verbose_name="Курс")
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    number = models.PositiveIntegerField("Номер урока")
    title_ru = models.CharField("Тема (рус)", max_length=200)
    title_kk = models.CharField("Тақырып (қаз)", max_length=200, blank=True)
    goal_ru = models.CharField("Цель (рус)", max_length=300, blank=True)
    goal_kk = models.CharField("Мақсат (қаз)", max_length=300, blank=True)
    # Теория - список блоков: {"p": [ru, kk]} абзац или {"code": "..."} пример кода
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
        return f"{self.user} - {self.task} - {'✓' if self.solved else '…'}"


def _class_code():
    import secrets
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # без похожих 0/O и 1/I
    return "".join(secrets.choice(alphabet) for _ in range(6))


class Classroom(models.Model):
    """Класс учителя: ученики вступают по коду и попадают в кабинет учителя."""
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="classrooms",
                                verbose_name="Учитель")
    name = models.CharField("Название", max_length=100)
    code = models.CharField("Код для вступления", max_length=8, unique=True, default=_class_code)
    # ученики такого класса получают доступ ко всем урокам без оплаты (включает только администратор)
    free_access = models.BooleanField("Бесплатный доступ для учеников", default=False)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Класс"
        verbose_name_plural = "Классы"

    def __str__(self):
        return f"{self.name} ({self.teacher})"


class Membership(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="memberships", verbose_name="Класс")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships",
                                verbose_name="Ученик")
    joined_at = models.DateTimeField("Вступил", auto_now_add=True)

    class Meta:
        unique_together = ("classroom", "student")
        ordering = ["joined_at"]
        verbose_name = "Ученик класса"
        verbose_name_plural = "Ученики классов"

    def __str__(self):
        return f"{self.student} → {self.classroom.name}"


def _cert_code():
    import secrets
    return secrets.token_hex(4).upper()


class Certificate(models.Model):
    """Сертификат о прохождении курса. Имя сохраняется на момент выдачи."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certificates",
                             verbose_name="Ученик")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="certificates", verbose_name="Курс")
    name = models.CharField("Имя на сертификате", max_length=200)
    teacher_name = models.CharField("Учитель", max_length=200, blank=True)
    code = models.CharField("Номер", max_length=12, unique=True, default=_cert_code)
    issued_at = models.DateTimeField("Выдан", auto_now_add=True)

    class Meta:
        unique_together = ("user", "course")
        ordering = ["-issued_at"]
        verbose_name = "Сертификат"
        verbose_name_plural = "Сертификаты"

    def __str__(self):
        return f"{self.name} - {self.course} ({self.code})"


class Subscription(models.Model):
    """Платный доступ ко всем курсам до даты paid_until (включительно)."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscription",
                                verbose_name="Ученик")
    paid_until = models.DateField("Оплачено до", null=True, blank=True)
    free = models.BooleanField("Бесплатный доступ", default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        return f"{self.user} до {self.paid_until}"


class Payment(models.Model):
    """Запись об оплате, которую отметил администратор (оплата приходит в Kaspi)."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments",
                             verbose_name="Ученик")
    amount = models.PositiveIntegerField("Сумма, ₸")
    months = models.PositiveIntegerField("Месяцев", default=1)
    paid_until = models.DateField("Доступ продлён до")
    note = models.CharField("Комментарий", max_length=200, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="+", verbose_name="Отметил")
    created_at = models.DateTimeField("Дата", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Оплата"
        verbose_name_plural = "Оплаты"

    def __str__(self):
        return f"{self.user} {self.amount} ₸ → {self.paid_until}"
