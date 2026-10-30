from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class CoreTests(TestCase):
    def test_signup_logs_in_and_redirects_to_course(self):
        r = self.client.post(reverse("signup"), {
            "first_name": "Айжан", "last_name": "Серикова", "username": "aizhan",
            "password1": "kodtap2026", "password2": "kodtap2026",
        })
        self.assertRedirects(r, reverse("course_home"))
        self.assertTrue(get_user_model().objects.filter(username="aizhan").exists())

    def test_language_switch(self):
        self.client.post(reverse("set_language"), {"lang": "kk", "next": "/"})
        r = self.client.get(reverse("course_home"))
        self.assertContains(r, "Балаларға")

    def test_language_switch_rejects_external_redirect(self):
        r = self.client.post(reverse("set_language"), {"lang": "ru", "next": "https://evil.example"})
        self.assertEqual(r["Location"], "/")
