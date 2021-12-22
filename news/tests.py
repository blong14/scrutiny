import datetime
import uuid
from typing import List, Optional
from unittest import mock

from django.http.response import HttpResponse
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.datetime_safe import new_datetime
from rest_framework.test import APIClient

from news.models import Item
from news.serializers import ItemSerializer
from scrutiny.tests import ScrutinyTestListView


def item(*args, **kwargs) -> Item:
    """Simple Item generator
    Saves single Item when called with pre-filled data
    TODO: Add proper test factories or fixtures
    """
    points = kwargs.pop("points", 77)
    now = datetime.datetime.now()
    i = Item(
        author="test_user",
        points=points,
        id=123,
        url="https://local.local",
        created_at=new_datetime(now),
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
        self.url = reverse("news_api.dashboard")
        self.items = [
            item(title="hello", points=100),
            item(title="hello again", points=50),
        ]

    def tearDown(self) -> None:
        self.model.objects.all().delete()

    def test_get_no_items(self):
        self.tearDown()
        with self.assertNumQueries(3):
            self.resp = self.client.get(self.url)
        self.assertEqual(self.resp.context["total"], 0)
        self.assertEqual(self.resp.context["new_today"], 0)
        self.assertEqual(self.resp.context["max_score"], 0)
        self.assertEqual(self.resp.context["max_score_slug"], "")

    def test_get(self):
        with self.assertNumQueries(3):
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
        self.url = self.item.get_absolute_url()
        self.items = [
            self.item,
        ]

    def tearDown(self) -> None:
        super().tearDown()
        self.model.objects.all().delete()

    def test_no_items(self) -> None:
        self.tearDown()
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 200)

    def test_items(self) -> None:
        super().test_items()
        self.assertContains(self.response, self.item.author)
        self.assertContains(self.response, self.item.points)
        self.assertContains(self.response, self.item.url)
        self.assertContains(self.response, self.item.title)

    def test_items_bad_request(self) -> None:
        self.url = f"{reverse('news.list_view')}?slugs=(SELECT * FROM news_item),(SELECT story FROM news_item)"
        self.response = self.client.get(path=self.url, format="json")
        self.assertEqual(self.response.status_code, 200)


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

    @mock.patch("news.signals.requests")
    def setUp(self, mock_requests) -> None:
        self.mock_requests = mock_requests
        self.mock_requests.post.return_value = HttpResponse(status=200)
        self.items = [
            item(title="hello"),
            item(title="hello again"),
        ]
        self.url = reverse("news_api.list_view")

    def tearDown(self) -> None:
        super().tearDown()
        if self.model:
            self.model.objects.all().delete()

    def test_no_items(self) -> None:
        self.tearDown()
        with self.assertNumQueries(1):
            self.response = self.client.get(path=self.url, format="json")
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(len(self.response.json()), 0)

    def test_items(self) -> None:
        with self.assertNumQueries(1):
            self.response = self.client.get(path=self.url, format="json")
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(len(self.response.json()), len(self.items))

    @mock.patch("news.signals.requests")
    def test_create_item(self, mock_requests):
        self.mock_requests = mock_requests
        self.tearDown()
        now = datetime.datetime.now()
        expected = self.model(
            author="test_user",
            points=77,
            id=123,
            url="https://local.local",
            created_at=new_datetime(now),
            title="hello",
            slug=str(uuid.uuid4()),
        )
        payload = [ItemSerializer(expected).data]
        resp = self.client.post(path=self.url, data=payload, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(
            self.model.objects.filter(slug=expected.slug).first(), expected
        )
        self.mock_requests.post.assert_called()

    @mock.patch("news.signals.requests")
    def test_create_items(self, mock_requests):
        self.mock_requests = mock_requests
        self.tearDown()
        now = datetime.datetime.now()
        data = [
            ItemSerializer(
                self.model(
                    author="test_user",
                    points=77,
                    id=123,
                    url="https://local.local",
                    created_at=new_datetime(now),
                    title="hello",
                    slug=str(uuid.uuid4()),
                ),
            ).data,
            ItemSerializer(
                self.model(
                    author="test_user",
                    points=77,
                    id=123,
                    url="https://local.local",
                    created_at=new_datetime(now),
                    title="ahello",
                    slug=str(uuid.uuid4()),
                ),
            ).data,
        ]
        resp = self.client.post(path=self.url, data=data, format="json")
        self.assertEqual(resp.status_code, 201)
        self.mock_requests.post.assert_called()
