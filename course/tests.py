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
        self.assertEqual(Lesson.objects.count(), 24)
        self.assertEqual(Lesson.objects.filter(is_project=True).count(), 5)
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
        self.assertEqual(self.client.get(reverse("course_home")).status_code, 200)
        r = self.client.get(reverse("course_lesson", args=[1]))
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
