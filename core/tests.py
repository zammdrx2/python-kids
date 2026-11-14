from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class CoreTests(TestCase):
    def test_signup_logs_in_and_redirects_to_course(self):
        r = self.client.post(reverse("signup"), {
            "first_name": "Айжан", "last_name": "Серикова", "username": "aizhan",
            "password1": "kodtap2026", "password2": "kodtap2026",
        })
        self.assertRedirects(r, reverse("home"))
        self.assertTrue(get_user_model().objects.filter(username="aizhan").exists())

    def test_language_switch(self):
        self.client.post(reverse("set_language"), {"lang": "kk", "next": "/"})
        r = self.client.get(reverse("home"))
        self.assertContains(r, "Балаларға")

    def test_language_switch_rejects_external_redirect(self):
        r = self.client.post(reverse("set_language"), {"lang": "ru", "next": "https://evil.example"})
        self.assertEqual(r["Location"], "/")


class FaviconTests(TestCase):
    def test_favicon(self):
        r = self.client.get("/favicon.ico")
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r["Location"].endswith("img/stack-favicon.ico"))
        self.assertContains(self.client.get(reverse("login")), "stack-icon.svg")


class SeoTests(TestCase):
    def test_meta_robots_sitemap(self):
        from django.core.management import call_command
        call_command("load_course", verbosity=0)
        r = self.client.get(reverse("home"))
        self.assertContains(r, 'property="og:image"')
        self.assertContains(r, "img/og-image.png")
        self.assertContains(r, 'name="description"')
        self.assertContains(self.client.get(reverse("course_home", args=["python"])), 'property="og:title" content="Python')
        r = self.client.get("/robots.txt")
        self.assertContains(r, "Disallow: /admin/")
        self.assertContains(r, "sitemap.xml")
        r = self.client.get("/sitemap.xml")
        self.assertContains(r, "/python/lesson/24/")
