from typing import List
from unittest import mock

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from social_django.models import UserSocialAuth

from scrutiny.tests import ScrutinyTestListView


class TestAnonymousUserListView(TestCase):
    client_class = Client

    def setUp(self) -> None:
        self.url = reverse("library.list_view")

    def test_get(self) -> None:
        self.resp = self.client.get(self.url, follow=True)
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, "registration/login.html")


class TestListView(ScrutinyTestListView):
    client_class = Client

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("library.list_view")
        self.items = {
            "list": {
                "0001": {"resolved_title": "Python can suck."},
                "002": {"resolved_title": "Django too."},
            }
        }
        self.user = User.objects.create_user("foo", "myemail@test.com", "pass")
        UserSocialAuth.objects.create(user=self.user, provider="pocket")
        self.client.login(username="foo", password="pass")

    def tearDown(self) -> None:
        super().tearDown()
        self.user.delete()

    @mock.patch("library.views.make_request")
    def test_no_items(self, mock_make_request) -> None:
        mock_make_request.return_value = {"list": []}
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 200)
        self.assertContains(self.response, "No items.")
        mock_make_request.assert_called()

    @mock.patch("library.views.make_request")
    def test_items(self, mock_make_request) -> None:
        mock_make_request.return_value = self.items
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(
            len(self.response.context["items"]), len(self.items.get("list").values())
        )
        self.assertListResponseContains(
            [item.get("resolved_title") for _, item in self.items.get("list").items()]
        )
        mock_make_request.assert_called()
