from platform import python_version
from typing import List

import django
from django.db import connection, models
from django.http.response import HttpResponse
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from .views import ScrutinyAboutView


class NoopClient(Client):
    def get(self, *args, **kwargs) -> HttpResponse:
        return HttpResponse(status=200)


class ScrutinyTestListView(TestCase):
    client_class = NoopClient
    items: List[models.Model]
    response: HttpResponse
    url: str

    def setUp(self) -> None:
        super().setUp()
        self.url = ""

    def test_no_items(self) -> None:
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 200)
        if not isinstance(self.client, NoopClient):
            self.assertContains(self.response, "No items.")

    def test_items(self) -> None:
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 200)
        if not isinstance(self.client, NoopClient):
            self.assertEqual(len(self.response.context["items"]), len(self.items))

    def assertListResponseContains(self, expected: List[str]) -> None:
        for item in expected:
            self.assertContains(self.response, item)


class TestScrutinyIndexView(TestCase):
    client_class = Client

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("scrutiny.index")

    def test_index(self) -> None:
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 200)
        self.assertTemplateUsed(self.response, "index.html")


class TestScrutinyAboutView(TestCase):
    client_class = Client

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("scrutiny.about")

    def test_about(self) -> None:
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 200)
        self.assertContains(self.response, django.get_version())
        self.assertContains(self.response, python_version())
        self.assertContains(self.response, ScrutinyAboutView.database_version())
        self.assertTemplateUsed(self.response, "about/index.html")
