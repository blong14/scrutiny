from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from social_django.models import UserSocialAuth

from .models import Article, Tag
from scrutiny.tests import ScrutinyTestListView


def article(**kwargs) -> Article:
    a = Article(
        authors={"1": "author"},
        listen_duration_estimate=100,
        **kwargs,
    )
    a.save()
    return a


def tag(**kwargs) -> Tag:
    a = Tag(
        **kwargs,
    )
    a.save()
    return a


class TestAnonymousUserListView(TestCase):
    client_class = Client

    def test_get_index(self) -> None:
        self.url = reverse("library")
        self.resp = self.client.get(self.url, follow=True)
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, "registration/login.html")

    def test_get_article_list(self) -> None:
        self.url = reverse("library.list_view")
        self.resp = self.client.get(self.url, follow=True)
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, "registration/login.html")

    def test_get_tag_list(self) -> None:
        self.url = reverse("library.tag_view")
        self.resp = self.client.get(self.url, follow=True)
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, "registration/login.html")


class TestIndexView(TestCase):
    client_class = Client

    def test_get(self) -> None:
        self.url = reverse("library")
        self.user = User.objects.create_user("foo", "myemail@test.com", "pass")
        UserSocialAuth.objects.create(user=self.user, provider="pocket")
        self.client.login(username="foo", password="pass")
        self.resp = self.client.get(self.url)
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, "library/index.html")


class TestListView(ScrutinyTestListView):
    client_class = Client
    model = Article

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("library.list_view")
        self.user = User.objects.create_user("foo", "myemail@test.com", "pass")
        self.items = [
            article(resolved_title="hello", user=self.user),
            article(resolved_title="hello 1", user=self.user),
            article(resolved_title="hello 2", user=self.user),
            article(resolved_title="world", user=self.user),
        ]
        UserSocialAuth.objects.create(user=self.user, provider="pocket")
        self.client.login(username="foo", password="pass")

    def tearDown(self) -> None:
        super().tearDown()
        self.model.objects.all().delete()

    def test_no_items(self) -> None:
        self.tearDown()
        super().test_no_items()

    def test_items(self) -> None:
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(len(self.response.context["items"]), len(self.items))
        self.assertListResponseContains([item.resolved_title for item in self.items])

    def test_items_search(self) -> None:
        url = reverse("library.list_view")
        self.response = self.client.get(f"{url}?search=world")
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(len(self.response.context["items"]), 1)
        self.assertListResponseContains(["world"])


class TestTagListView(ScrutinyTestListView):
    client_class = Client
    model = Tag

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("library.tag_view")
        self.user = User.objects.create_user("foo", "myemail@test.com", "pass")
        art = article(user=self.user)
        self.items = [
            tag(value="foobar", user=self.user, article=art),
            tag(value="foobar 1", user=self.user, article=art),
            tag(value="foobar 2", user=self.user, article=art),
        ]
        UserSocialAuth.objects.create(user=self.user, provider="pocket")
        self.client.login(username="foo", password="pass")

    def tearDown(self) -> None:
        super().tearDown()
        self.model.objects.all().delete()

    def test_no_items(self) -> None:
        self.tearDown()
        super().test_no_items()

    def test_items(self) -> None:
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(len(self.response.context["items"]), len(self.items))
        self.assertListResponseContains([item.value for item in self.items])
