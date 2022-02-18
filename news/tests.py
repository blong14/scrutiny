import uuid
from typing import List, Optional

from django.http.response import HttpResponse
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.timezone import now as utc_now
from rest_framework.test import APIClient

from news.models import Event, Item
from news.serializers import ItemSerializer
from scrutiny.tests import ScrutinyTestListView


def item(*args, **kwargs) -> Item:
    """Simple Item generator
    Saves single Item when called with pre-filled data
    TODO: Add proper test factories or fixtures
    """
    points = kwargs.pop("points", 77)
    author = kwargs.pop("author", "test_user")
    i = Item(
        author=author,
        points=points,
        url="https://local.local",
        created_at=utc_now(),
        slug=str(uuid.uuid4()),
        *args,
        **kwargs,
    )
    i.save()
    return i


class TestApiDashboardView(TestCase):
    client_class = Client
    model = Item

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("news_api.dashboard")
        self.items = [
            item(title="hello", points=100),
            item(title="hello again", points=50),
        ]
        self.user = User.objects.create_superuser("foo", "myemail@test.com", "pass")
        self.client.login(username="foo", password="pass")

    def tearDown(self) -> None:
        super().tearDown()
        self.model.objects.all().delete()

    def test_get_no_items(self):
        self.tearDown()
        with self.assertNumQueries(5):
            self.resp = self.client.get(self.url)
        self.assertEqual(self.resp.context["total"], 0)
        self.assertEqual(self.resp.context["new_today"], 0)
        self.assertEqual(self.resp.context["max_score"], 0)
        self.assertEqual(self.resp.context["max_score_slug"], "")

    def test_get(self):
        with self.assertNumQueries(5):
            self.resp = self.client.get(self.url)
        self.assertContains(self.resp, "Total")
        self.assertEqual(self.resp.context["total"], len(self.items))
        self.assertContains(self.resp, "data-total-value")
        self.assertContains(self.resp, "New Today")
        self.assertEqual(self.resp.context["new_today"], 2)
        self.assertContains(self.resp, "data-new-today")
        self.assertContains(self.resp, "Highest Score")
        self.assertEqual(self.resp.context["max_score"], 100)
        self.assertContains(self.resp, "data-max-score")
        self.assertEqual(
            self.resp.context["max_score_slug"],
            self.model.objects.get(title="hello").slug,
        )


class TestListViewWithDetails(ScrutinyTestListView):
    client_class = Client
    model = Item

    def setUp(self) -> None:
        super().setUp()
        self.item = item(title="Python can suck.")
        self.comment = item(
            author="comment author",
            parent=self.item,
            text="comment text",
            title="comment",
            type="COMMENT",
        )
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
        comment = item(
            author="comment author",
            parent=self.item,
            text="",  # should not display this comment as it is missing text
            title="comment",
            type="COMMENT",
        )
        super().test_items()
        self.assertContains(self.response, self.item.slug)
        self.assertContains(self.response, self.item.author)
        self.assertContains(self.response, self.item.url)
        self.assertContains(self.response, self.item.title)
        self.assertContains(self.response, self.comment.slug)
        self.assertContains(self.response, self.comment.author)
        self.assertContains(self.response, self.comment.text)
        self.assertNotContains(self.response, comment.slug)

    def test_items_bad_request(self) -> None:
        self.url = f"{reverse('news.list_view')}?slugs=(SELECT * FROM news_item),(SELECT story FROM news_item)"
        self.response = self.client.get(path=self.url, format="json")
        self.assertEqual(self.response.status_code, 200)


class TestAnonymousUserListView(TestCase):
    client_class = Client

    def setUp(self) -> None:
        self.url = reverse("news.list_view")

    def test_get(self) -> None:
        self.resp = self.client.get(self.url, follow=True)
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, "registration/login.html")


class TestListView(ScrutinyTestListView):
    client_class = Client
    model = Item

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("news.list_view")
        self.items: List[Item] = [
            item(title="Python can suck."),
            item(title="Django too"),
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
        self.assertListResponseContains([item.title for item in self.items])
        self.assertListResponseContains(
            [item.get_absolute_url() for item in self.items]
        )


class TestApiListView(TestCase):
    client_class = APIClient
    items = List[Item]
    model = Item
    response: HttpResponse
    url: Optional[str] = ""

    def setUp(self) -> None:
        item(title="hello, no children")
        self.item = item(title="hello")
        self.items = [
            item(title="hello again", parent=self.item),
            item(title="hello again 2", parent=self.item),
        ]
        self.url = reverse("news_api.list_view")

    def tearDown(self) -> None:
        super().tearDown()
        if self.model:
            self.model.objects.all().delete()
        Event.objects.all().delete()

    def test_no_items(self) -> None:
        self.tearDown()
        with self.assertNumQueries(1):
            self.response = self.client.get(path=self.url, format="json")
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response.json()["count"], 0)

    def test_items(self) -> None:
        with self.assertNumQueries(3):
            self.response = self.client.get(path=self.url, format="json")
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response.json()["count"], len(self.items))

    def test_create_item(self):
        self.tearDown()
        expected = self.model(
            id=123,
            author="test_user",
            points=77,
            url="https://local.local",
            created_at=utc_now(),
            title="hello",
            slug=str(uuid.uuid4()),
        )
        payload = ItemSerializer(expected).data
        self.assertIsNone(Event.objects.first())
        resp = self.client.post(path=self.url, data=payload, format="json")
        actual = self.model.objects.filter(slug=expected.slug).first()
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(actual.slug, expected.slug)
        self.assertEqual(Event.objects.first().event_type, "STORY_ADDED")
