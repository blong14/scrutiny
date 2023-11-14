from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from social_django.models import UserSocialAuth

from .models import Job


class TestListView(TestCase):
    client_class = Client
    model = Job

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("jobs")
        self.user = User.objects.create_user("foo", "myemail@test.com", "pass")
        self.items = []
        UserSocialAuth.objects.create(user=self.user, provider="pocket")
        self.client.login(username="foo", password="pass")

    def tearDown(self) -> None:
        super().tearDown()
        self.model.objects.all().delete()

    def test_anonymous_user(self):
        self.client.logout()
        self.resp = self.client.get(self.url, follow=True)
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, "registration/login.html")

    def test_no_items(self) -> None:
        self.tearDown()
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 200)
        self.assertContains(self.response, "No items.")


class TestCreateView(TestCase):
    client_class = Client
    model = Job

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("job_create")
        self.user = User.objects.create_user("foo", "myemail@test.com", "pass")
        self.items = []
        UserSocialAuth.objects.create(user=self.user, provider="pocket")
        self.client.login(username="foo", password="pass")

    def tearDown(self) -> None:
        super().tearDown()
        self.model.objects.all().delete()

    def test_create(self) -> None:
        self.resp = self.client.post(
            self.url,
            data={
                "name": "test_job",
                "data": {
                    "feed_id": "hackernews",
                    "title": "Example News Item",
                    "url": "https://article.com",
                },
            },
        )
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, "jobs/job_form.html")
