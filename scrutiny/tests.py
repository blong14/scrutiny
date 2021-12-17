from typing import List, Optional

from django.db import models
from django.http.response import HttpResponse
from django.test import TestCase
from django.test.client import Client


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
            self.assertNumQueries(1)
            self.assertEqual(len(self.response.context["items"]), len(self.items))

    def assertListResponseContains(self, expected: List[str]) -> None:
        for item in expected:
            self.assertContains(self.response, item)


class ScrutinyTestApiListView(TestCase):
    client_class = NoopClient
    items: List[models.Model]
    model: Optional[models.Model] = None
    url: Optional[str] = ""
    response: HttpResponse

    def tearDown(self) -> None:
        super().tearDown()
        if self.model:
            self.model.objects.all().delete()

    def test_no_items(self) -> None:
        self.tearDown()
        self.response = self.client.get(path=self.url, format="json")
        if not isinstance(self.client, NoopClient):
            self.assertNumQueries(1)
            self.assertEqual(self.response.status_code, 200)
            self.assertEqual(len(self.response.json()), 0)

    def test_items(self) -> None:
        self.response = self.client.get(path=self.url, format="json")
        if not isinstance(self.client, NoopClient):
            self.assertEqual(self.response.status_code, 200)
            self.assertNumQueries(1)
            self.assertEqual(len(self.response.json()), len(self.items))
