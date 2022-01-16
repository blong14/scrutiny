from typing import List

from django.contrib.auth.models import User
from django.test.client import Client
from django.urls import reverse

from library.models import Article
from scrutiny.tests import ScrutinyTestListView


def article(*args, **kwargs) -> Article:
    art = Article(*args, **kwargs)
    art.save()
    return art


class TestListView(ScrutinyTestListView):
    client_class = Client

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("library.list_view")
        self.items: List[Article] = [
            article(title=title) for title in ("Python can suck.", "Django too.")
        ]
        self.user = User.objects.create_superuser("foo", "myemail@test.com", "pass")
        self.client.login(username="foo", password="pass")

    def tearDown(self) -> None:
        super().tearDown()
        Article.objects.all().delete()

    def test_no_items(self) -> None:
        self.tearDown()
        super().test_no_items()

    def test_items(self) -> None:
        super().test_items()
        self.assertListResponseContains([item.title for item in self.items])
