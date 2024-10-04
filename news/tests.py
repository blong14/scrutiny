from unittest import mock

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import FeedRegistry, FeedResponse


class TestListView(TestCase):
    client_class = Client

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("news")
        self.user = User.objects.create_superuser("foo", "myemail@test.com", "pass")
        self.client.login(username="foo", password="pass")

    def test_list_anonymous_user(self) -> None:
        self.client.logout()
        self.resp = self.client.get(self.url, follow=True)
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, "registration/login.html")

    def test_list(self) -> None:
        self.resp = self.client.get(self.url)
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, "news/list.html")
        for feed in FeedRegistry.feeds():
            self.assertContains(self.resp, feed.id)
            self.assertContains(self.resp, feed.title)


class TestFeedView(TestCase):
    client_class = Client

    def setUp(self) -> None:
        super().setUp()
        self.url = f"{reverse('news.feed_view')}?feed=hackernews"
        self.user = User.objects.create_superuser("foo", "myemail@test.com", "pass")
        self.client.login(username="foo", password="pass")

    def test_feeds_anonymous_user(self) -> None:
        self.client.logout()
        self.resp = self.client.get(self.url, follow=True)
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, "registration/login.html")

    def test_missing_feed(self) -> None:
        self.url = f"{reverse('news.feed_view')}?feed=missing"
        self.resp = self.client.get(self.url, follow=True)
        self.assertEqual(self.resp.status_code, 404)

    @mock.patch("news.views.default_parser.parse")
    def test_feeds(self, mock_parse) -> None:
        feeds = {
            feed.id: f"{reverse('news.feed_view')}?feed={feed.id}"
            for feed in FeedRegistry.feeds()
        }
        for feed, url in feeds.items():
            mock_parse.return_value = FeedResponse(
                entries=[
                    {"title": "hello", "link": "test.link", "comments": "comments.link"}
                ]
            )  # noqa
            self.resp = self.client.get(url)
            self.assertEqual(self.resp.status_code, 200)
            self.assertTemplateUsed(self.resp, "news/list.html")
            self.assertContains(self.resp, feed)
            self.assertContains(self.resp, "hello")


class TestNewsItemFormView(TestCase):
    client_class = Client

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("news.save_view")
        self.user = User.objects.create_superuser("foo", "myemail@test.com", "pass")
        self.client.login(username="foo", password="pass")

    def test_save_anonymous_user(self) -> None:
        self.client.logout()
        self.resp = self.client.post(self.url, follow=True)
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, "registration/login.html")

    @mock.patch("jobs.signals.requests.post")
    def test_save(self, mock_post) -> None:
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            "item": {
                "item_id": "111",
                "title": "Example News Item",
            },
        }
        self.resp = self.client.post(
            self.url,
            data={
                "feed_id": "hackernews",
                "title": "Example News Item",
                "url": "https://article.com",
            },
        )
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, "news/list.html")
        self.assertEqual(self.resp.context["selected"], "Example News Item")
        mock_post.assert_called()


class TestNewsSummaryView(TestCase):
    client_class = Client

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("news.summary_view")
        self.user = User.objects.create_superuser("foo", "myemail@test.com", "pass")
        self.client.login(username="foo", password="pass")

    def test_get_anonymous_user(self) -> None:
        self.client.logout()
        self.resp = self.client.get(self.url, follow=True)
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, "registration/login.html")

    @mock.patch("news.views.publisher")
    def test_get(self, mock_publisher) -> None:
        mock_publisher.publish.return_value = True
        self.resp = self.client.get(
            self.url, data={"feed_id": "hackernews"},
        )
        self.assertEqual(self.resp.status_code, 200)
        self.assertTemplateUsed(self.resp, "news/news_summary.html")
        self.assertEqual(self.resp.context["summary"], "Loading...")
