from typing import List

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note, Project
from scrutiny.tests import ScrutinyTestListView


def project(*args, **kwargs) -> Project:
    pr = Project(
        *args,
        **kwargs,
    )
    pr.save()
    note = Note(
        title="hh",
        body="a body",
        project=pr,
    )
    note.save()
    return pr


class TestAnonymousUserView(TestCase):
    client_class = Client

    def setUp(self) -> None:
        super().setUp()
        self.urls = [
            reverse("notes_api.dashboard"),
            reverse("notes.list_view"),
            reverse("notes.detail_view", args=["foobar"]),
        ]

    def test_get(self) -> None:
        for url in self.urls:
            self.resp = self.client.get(url, follow=True)
            self.assertEqual(self.resp.status_code, 200)
            self.assertTemplateUsed(self.resp, "registration/login.html")


class TestDashboardView(TestCase):
    client_class = Client
    model = Project

    def setUp(self) -> None:
        self.url = reverse("notes_api.dashboard")
        self.user = User.objects.create_superuser("foo", "myemail@test.com", "pass")
        self.items = [
            project(title="hello", user=self.user),
            project(title="hello again", user=self.user),
        ]
        self.client.login(username="foo", password="pass")

    def tearDown(self) -> None:
        self.model.objects.all().delete()

    def test_get_no_items(self):
        self.tearDown()
        with self.assertNumQueries(4):
            self.resp = self.client.get(self.url)
        self.assertEqual(self.resp.context["total_projects"], 0)
        self.assertEqual(self.resp.context["total_notes"], 0)

    def test_get(self):
        with self.assertNumQueries(4):
            self.resp = self.client.get(self.url)
        self.assertContains(self.resp, "Total")
        self.assertEqual(self.resp.context["total_projects"], len(self.items))
        self.assertContains(self.resp, "data-total-projects")
        self.assertContains(self.resp, "Total Notes")
        self.assertEqual(self.resp.context["total_notes"], 2)
        self.assertContains(self.resp, "data-total-notes")


class TestListView(ScrutinyTestListView):
    client_class = Client

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("notes.list_view")
        self.user = User.objects.create_superuser("foo", "myemail@test.com", "pass")
        self.items: List[Project] = [
            project(id=123, title="project_1", slug="foo", user=self.user),
            project(id=456, title="project_2", slug="bar", user=self.user),
        ]
        self.client.login(username="foo", password="pass")

    def tearDown(self) -> None:
        super().tearDown()
        Project.objects.all().delete()
        Note.objects.all().delete()

    def test_no_items(self) -> None:
        self.tearDown()
        super().test_no_items()

    def test_items(self) -> None:
        super().test_items()
        self.assertListResponseContains([item.title for item in self.items])

    def test_get_not_authorized(self) -> None:
        self.client.logout()
        user = User.objects.create_superuser("foobars", "myemail@test.com", "pass")
        self.client.login(username=user.username, password="pass")
        self.resp = self.client.get(self.url)
        self.assertEqual(self.resp.status_code, 200)
        self.assertEqual(len(self.resp.context["items"]), 0)


class TestDetailView(TestCase):
    client_class = Client
    model = Project

    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.create_superuser("foo", "myemail@test.com", "pass")
        self.item = project(title="Python can suck.", slug="bar", user=self.user)
        self.url = self.item.get_absolute_url
        self.client.login(username="foo", password="pass")

    def tearDown(self) -> None:
        super().tearDown()
        self.model.objects.all().delete()

    def test_get(self) -> None:
        self.resp = self.client.get(self.url)
        self.assertContains(self.resp, self.item.slug)
        self.assertContains(self.resp, self.item.title)
        for note in self.item.notes.all():
            self.assertContains(self.resp, note.slug)
            self.assertContains(self.resp, note.title)

    def test_get_not_authorized(self) -> None:
        self.client.logout()
        user = User.objects.create_superuser("foobars", "myemail@test.com", "pass")
        self.client.login(username=user.username, password="pass")
        self.resp = self.client.get(self.url)
        self.assertEqual(self.resp.status_code, 404)
