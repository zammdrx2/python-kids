import json

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .data.build.build import normalize, run
from .models import Lesson, Submission, Task
from .services import record_submission


class CourseContentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("load_course", verbosity=0)

    def test_24_lessons_loaded(self):
        self.assertEqual(Lesson.objects.filter(course__slug="python").count(), 24)
        self.assertEqual(Lesson.objects.filter(course__slug="web").count(), 24)
        for lesson in Lesson.objects.filter(course__slug="python"):
            self.assertGreaterEqual(lesson.tasks.count(), 6, lesson)
        self.assertEqual(Lesson.objects.filter(course__slug="python", is_project=True).count(), 5)
        self.assertTrue(all(t.tests for t in Task.objects.filter(kind=Task.Kind.WEB)))
        self.assertEqual(Task.objects.filter(kind=Task.Kind.WEB).count(), 120)
        self.assertEqual(Task.objects.filter(kind=Task.Kind.PROJECT).count(), 6)

    def test_every_solution_passes_its_tests(self):
        for task in Task.objects.filter(kind=Task.Kind.TESTED):
            self.assertTrue(task.tests, task)
            for t in task.tests:
                self.assertEqual(normalize(run(task.solution, t["input"])), normalize(t["output"]), task)

    def test_reload_keeps_submissions(self):
        user = get_user_model().objects.create_user("kid", password="x")
        task = Task.objects.filter(kind=Task.Kind.TESTED).first()
        record_submission(user, task, "print(1)", 0, 99)
        call_command("load_course", verbosity=0)
        self.assertEqual(Submission.objects.count(), 1)


class SubmissionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("load_course", verbosity=0)
        cls.user = get_user_model().objects.create_user("kid", password="pass12345")
        cls.task = Task.objects.filter(kind=Task.Kind.TESTED).first()
        cls.project = Task.objects.filter(kind=Task.Kind.PROJECT).first()

    def test_total_comes_from_server_and_passed_clamped(self):
        sub = record_submission(self.user, self.task, "x", 50, 50)
        self.assertEqual(sub.total_tests, len(self.task.tests))
        self.assertEqual(sub.passed_tests, len(self.task.tests))
        self.assertTrue(sub.solved)

    def test_failed_attempt_does_not_unsolve(self):
        n = len(self.task.tests)
        record_submission(self.user, self.task, "good", n, n)
        sub = record_submission(self.user, self.task, "bad", 0, n)
        self.assertTrue(sub.solved)
        self.assertEqual(sub.attempts, 2)

    def test_project_needs_changed_code(self):
        sub = record_submission(self.user, self.project, self.project.starter_code, 1, 1)
        self.assertFalse(sub.solved)
        sub = record_submission(self.user, self.project, self.project.starter_code + "\nprint('мой код')", 1, 1)
        self.assertTrue(sub.solved)

    def test_pages_and_submit_view(self):
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)
        self.assertEqual(self.client.get(reverse("course_home", args=["python"])).status_code, 200)
        self.assertEqual(self.client.get(reverse("course_module", args=["python", 2])).status_code, 200)
        self.assertEqual(self.client.get(reverse("course_module", args=["python", 99])).status_code, 404)
        r = self.client.get(reverse("course_lesson", args=["python", 1]))
        self.assertContains(r, "print")
        url = reverse("course_submit", args=[self.task.id])
        self.assertEqual(self.client.post(url, "{}", content_type="application/json").status_code, 302)
        self.client.login(username="kid", password="pass12345")
        n = len(self.task.tests)
        r = self.client.post(url, json.dumps({"code": "print()", "passed": n}), content_type="application/json")
        self.assertEqual(r.json()["solved"], True)

    def test_progress_page_staff_only(self):
        self.client.login(username="kid", password="pass12345")
        self.assertEqual(self.client.get(reverse("course_progress")).status_code, 302)


class LessonLockTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("load_course", verbosity=0)
        cls.user = get_user_model().objects.create_user("kid2", password="pass12345")
        cls.teacher = get_user_model().objects.create_user("teacher", password="pass12345", is_staff=True)

    def test_next_lesson_locked_until_previous_done(self):
        self.client.login(username="kid2", password="pass12345")
        r = self.client.get(reverse("course_lesson", args=["python", 2]))
        self.assertRedirects(r, reverse("course_module", args=["python", 1]))
        task2 = Task.objects.filter(lesson__number=2).first()
        r = self.client.post(reverse("course_submit", args=[task2.id]), json.dumps({"code": "x", "passed": 1}),
                             content_type="application/json")
        self.assertEqual(r.status_code, 403)
        for t in Task.objects.filter(lesson__number=1):
            record_submission(self.user, t, (t.starter_code or "") + "\nprint(1)", len(t.tests), len(t.tests))
        self.assertEqual(self.client.get(reverse("course_lesson", args=["python", 2])).status_code, 200)
        self.assertEqual(self.client.get(reverse("course_lesson", args=["python", 3])).status_code, 302)

    def test_guest_sees_only_first_lesson(self):
        self.assertEqual(self.client.get(reverse("course_lesson", args=["python", 1])).status_code, 200)
        self.assertEqual(self.client.get(reverse("course_lesson", args=["python", 2])).status_code, 302)

    def test_teacher_sees_everything(self):
        self.client.login(username="teacher", password="pass12345")
        self.assertEqual(self.client.get(reverse("course_lesson", args=["python", 24])).status_code, 200)


class MultiCourseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("load_course", verbosity=0)
        cls.user = get_user_model().objects.create_user("kid3", password="pass12345")

    def test_course_pages(self):
        r = self.client.get(reverse("home"))
        self.assertContains(r, "HTML")
        self.assertEqual(self.client.get(reverse("course_home", args=["web"])).status_code, 200)
        self.assertEqual(self.client.get(reverse("course_home", args=["nope"])).status_code, 404)
        r = self.client.get(reverse("course_lesson", args=["web", 1]))
        self.assertContains(r, "iframe")
        self.assertContains(self.client.get(reverse("course_lesson", args=["js", 1])), "jsworker.js")
        self.assertContains(self.client.get(reverse("course_lesson", args=["sql", 1])), "sql-wasm.js")
        self.assertEqual(Lesson.objects.filter(course__slug="js").count(), 24)
        self.assertEqual(Lesson.objects.filter(course__slug="sql").count(), 24)

    def test_legacy_urls_redirect_to_python(self):
        r = self.client.get("/lesson/1/")
        self.assertRedirects(r, reverse("course_lesson", args=["python", 1]), status_code=301)

    def test_locks_are_per_course(self):
        self.client.login(username="kid3", password="pass12345")
        for t in Task.objects.filter(lesson__course__slug="python", lesson__number=1):
            record_submission(self.user, t, "x\nprint(1)", len(t.tests), len(t.tests))
        # первый урок веб-курса открыт, второй — нет, несмотря на прогресс в Python
        self.assertEqual(self.client.get(reverse("course_lesson", args=["web", 1])).status_code, 200)
        self.assertEqual(self.client.get(reverse("course_lesson", args=["web", 2])).status_code, 302)


class OfficeCourseTests(TestCase):
    """Курсы Word, Excel, PowerPoint: тесты и файлы проверяет сервер."""

    @classmethod
    def setUpTestData(cls):
        call_command("load_course", verbosity=0)
        cls.user = get_user_model().objects.create_user("kid5", password="pass12345")

    def test_courses_loaded(self):
        for slug in ("word", "excel", "powerpoint"):
            self.assertEqual(Lesson.objects.filter(course__slug=slug).count(), 12)
            for lesson in Lesson.objects.filter(course__slug=slug):
                self.assertEqual(lesson.tasks.filter(kind=Task.Kind.QUIZ).count(), 4, lesson)
                self.assertEqual(lesson.tasks.filter(kind=Task.Kind.FILE).count(), 2, lesson)

    def quiz(self):
        return Task.objects.filter(kind=Task.Kind.QUIZ, lesson__course__slug="word", lesson__number=1).first()

    def test_quiz_answer_not_on_page_and_checked_on_server(self):
        task = self.quiz()
        right = task.tests[0]["answer"]
        r = self.client.get(reverse("course_lesson", args=["word", 1]))
        self.assertContains(r, task.tests[0]["options"][0][0])
        self.assertNotContains(r, '"answer"')
        url = reverse("course_submit", args=[task.id])
        # гость может проверить ответ, но ничего не сохраняется
        r = self.client.post(url, json.dumps({"choice": right}), content_type="application/json")
        self.assertTrue(r.json()["correct"])
        self.assertEqual(Submission.objects.count(), 0)
        self.client.login(username="kid5", password="pass12345")
        # подделать «passed» нельзя — важен только выбранный вариант
        wrong = (right + 1) % len(task.tests[0]["options"])
        r = self.client.post(url, json.dumps({"choice": wrong, "passed": 1}), content_type="application/json")
        self.assertFalse(r.json()["correct"])
        self.assertFalse(Submission.objects.get(user=self.user, task=task).solved)
        r = self.client.post(url, json.dumps({"choice": right}), content_type="application/json")
        self.assertTrue(Submission.objects.get(user=self.user, task=task).solved)
        self.assertEqual(self.client.post(url, json.dumps({"choice": 99}), content_type="application/json").status_code, 400)

    def test_file_upload_checked(self):
        import sys
        from pathlib import Path

        from django.core.files.uploadedfile import SimpleUploadedFile
        sys.path.insert(0, str(Path(__file__).parent / "data" / "build"))
        from office_make import make_blank, make_solution

        self.client.login(username="kid5", password="pass12345")
        for slug, kind, ext in (("word", "word", "docx"), ("excel", "excel", "xlsx"), ("powerpoint", "pptx", "pptx")):
            task = Task.objects.filter(kind=Task.Kind.FILE, lesson__course__slug=slug, lesson__number=1).first()
            url = reverse("course_submit", args=[task.id])
            r = self.client.post(url, {"file": SimpleUploadedFile(f"a.{ext}", make_blank(kind))})
            self.assertFalse(r.json()["solved"], slug)
            self.assertTrue(any(not x["ok"] for x in r.json()["results"]))
            r = self.client.post(url, {"file": SimpleUploadedFile(f"a.{ext}", make_solution(kind, task.tests))})
            self.assertTrue(r.json()["solved"], (slug, r.json()))
            self.assertTrue(Submission.objects.get(user=self.user, task=task).solved)
            r = self.client.post(url, {"file": SimpleUploadedFile("a.txt", b"hello")})
            self.assertEqual(r.status_code, 400)
            r = self.client.post(url, {"file": SimpleUploadedFile(f"a.{ext}", b"not a zip")})
            self.assertEqual(r.status_code, 400)
        r = self.client.get(reverse("course_lesson", args=["excel", 1]))
        self.assertContains(r, 'accept=".xlsx"')
