from typing import List

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from notes.management.commands.sync import Command
from notes.models import Note, Project
from scrutiny.tests import ScrutinyTestListView


def project(*args, **kwargs) -> Project:
    note = Note(
        title="hh",
        body="a body",
    )
    note.save()
    pr = Project(
        *args,
        **kwargs,
    )
    pr.save()
    pr.notes.set([note])
    return pr


class TestAnonymousUserListView(TestCase):
    client_class = Client

    def setUp(self) -> None:
        self.url = reverse("notes.list_view")

    def test_get(self) -> None:
        self.resp = self.client.get(self.url, follow=True)
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, "registration/login.html")


class TestGraftApiDashboardView(TestCase):
    client_class = Client
    model = Project

    def setUp(self) -> None:
        self.url = reverse("notes_api.dashboard")
        self.items = [
            project(title="hello"),
            project(title="hello again"),
        ]
        self.user = User.objects.create_superuser("foo", "myemail@test.com", "pass")
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


class TestListViewWithDetails(ScrutinyTestListView):
    client_class = Client
    model = Project

    def setUp(self) -> None:
        super().setUp()
        self.item = project(title="Python can suck.")
        self.url = self.item.get_absolute_url()
        self.items = [
            self.item,
        ]
        self.user = User.objects.create_superuser("foo", "myemail@test.com", "pass")
        self.client.login(username="foo", password="pass")

    def tearDown(self) -> None:
        super().tearDown()
        self.model.objects.all().delete()

    def test_no_items(self) -> None:
        self.tearDown()
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 200)

    def test_items(self) -> None:
        super().test_items()
        self.assertContains(self.response, self.item.slug)
        self.assertContains(self.response, self.item.title)
        for note in self.item.notes.all():
            self.assertContains(self.response, note.slug)
            self.assertContains(self.response, note.body)


class TestListView(ScrutinyTestListView):
    client_class = Client

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("notes.list_view")
        self.items: List[Project] = [
            project(id=123, title="project_1"),
            project(id=456, title="project_2"),
        ]
        self.user = User.objects.create_superuser("foo", "myemail@test.com", "pass")
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
