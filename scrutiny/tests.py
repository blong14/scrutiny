from typing import List

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
