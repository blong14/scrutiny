from platform import python_version

import django
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from .views import ScrutinyAboutView


class TestScrutinyIndexView(TestCase):
    client_class = Client

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("index")

    def test_index(self) -> None:
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 200)
        self.assertTemplateUsed(self.response, "index.html")


class TestScrutinyAboutView(TestCase):
    client_class = Client

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("about")

    def test_about(self) -> None:
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 200)
        self.assertContains(self.response, django.get_version())
        self.assertContains(self.response, python_version())
        self.assertContains(self.response, ScrutinyAboutView.database_version())
        self.assertTemplateUsed(self.response, "about/index.html")
