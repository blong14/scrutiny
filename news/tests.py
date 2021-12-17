import datetime
import uuid
from typing import List

from django.utils.datetime_safe import new_datetime
from django.test import Client
from django.urls import reverse
from rest_framework.test import APIClient

from news.models import Article
from news.serializers import ArticleSerializer
from scrutiny.tests import ScrutinyTestApiListView, ScrutinyTestListView


def article(*args, **kwargs) -> Article:
    """Simple Article generator
    Saves single Article when called with pre-filled data
    TODO: Add proper test factories or fixtures
    """
    now = datetime.datetime.now()
    art = Article(
        posted_by="test_user",
        score=77,
        story_id=123,
        story_url="https://local.local",
        time=new_datetime(now),
        slug=str(uuid.uuid4()),
    )
    art.save()
    return art


class TestListViewWithDetails(ScrutinyTestListView):
    client_class = Client

    def setUp(self) -> None:
        super().setUp()
        self.item = article(title="Python can suck.")
        self.url = self.item.get_absolute_url()
        self.items = [
            self.item,
        ]

    def tearDown(self) -> None:
        super().tearDown()
        Article.objects.all().delete()

    def test_no_items(self) -> None:
        self.tearDown()
        super().test_no_items()

    def test_items(self) -> None:
        super().test_items()
        self.assertContains(self.response, self.item.posted_by)
        self.assertContains(self.response, self.item.score)
        self.assertContains(self.response, self.item.story_url)
        self.assertContains(self.response, self.item.title)

    def test_items_bad_request(self) -> None:
        self.url = f"{reverse('news.list_view')}?slugs=(SELECT * FROM news_article),(SELECT story FROM news_article)"
        self.response = self.client.get(path=self.url, format="json")
        self.assertEqual(self.response.status_code, 200)


class TestListView(ScrutinyTestListView):
    client_class = Client

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("news.list_view")
        self.items: List[Article] = [
            article(title="Python can suck."),
            article(title="Django too"),
        ]

    def tearDown(self) -> None:
        super().tearDown()
        Article.objects.all().delete()

    def test_no_items(self) -> None:
        self.tearDown()
        super().test_no_items()

    def test_items(self) -> None:
        super().test_items()
        self.assertListResponseContains([item.title for item in self.items])
        self.assertListResponseContains(
            [item.get_absolute_url() for item in self.items]
        )


class TestApiListView(ScrutinyTestApiListView):
    client_class = APIClient
    items = List[Article]
    model = Article

    def setUp(self) -> None:
        self.items = [
            article(title="hello"),
            article(title="hello again"),
        ]
        self.url = reverse("news_api.list_view")

    def test_create_item(self):
        now = datetime.datetime.now()
        expected = Article(
            posted_by="test_user",
            score=77,
            story_id=123,
            story_url="https://local.local",
            time=new_datetime(now),
            title="hello",
            slug=str(uuid.uuid4()),
        )
        payload = [ArticleSerializer(expected).data]
        resp = self.client.post(path=self.url, data=payload, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Article.objects.filter(slug=expected.slug).first(), expected)

    def test_create_items(self):
        now = datetime.datetime.now()
        data = [
            ArticleSerializer(
                Article(
                    posted_by="test_user",
                    score=77,
                    story_id=123,
                    story_url="https://local.local",
                    time=new_datetime(now),
                    title="hello",
                    slug=str(uuid.uuid4()),
                ),
            ).data,
            ArticleSerializer(
                Article(
                    posted_by="test_user",
                    score=77,
                    story_id=123,
                    story_url="https://local.local",
                    time=new_datetime(now),
                    title="ahello",
                    slug=str(uuid.uuid4()),
                ),
            ).data,
        ]
        resp = self.client.post(path=self.url, data=data, format="json")
        self.assertEqual(resp.status_code, 201)
