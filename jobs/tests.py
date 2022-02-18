from django.test import Client, TestCase
from django.urls import reverse
from django.utils.timezone import now as utc_now

from jobs.models import Job
from jobs.serializers import JobSerializer


class TestJobsStatusView(TestCase):
    client_class = Client
    model = Job

    def setUp(self) -> None:
        now = utc_now()
        self.url = reverse("jobs_api.dashboard")
        self.item = Job(name="hackernews", synced_at=now)
        self.item.save()

    def tearDown(self) -> None:
        self.model.objects.all().delete()

    def test_get(self):
        with self.assertNumQueries(1):
            self.resp = self.client.get(f"{self.url}?name=hackernews")
        self.assertContains(self.resp, "data-last-sync")
        self.assertEqual(self.resp.context["last_sync"], self.item.synced_at)
        self.assertContains(self.resp, "data-status")
        self.assertEqual(self.resp.context["status"], self.item.status)


class TestJobsStatusUpdate(TestCase):
    client_class = Client
    model = Job

    def setUp(self) -> None:
        now = utc_now()
        self.item = Job(
            name="hackernews",
            status="Healthy",
            synced_at=now,
        )
        self.item.save()

    def tearDown(self) -> None:
        self.model.objects.all().delete()

    def test_put(self):
        self.assertEqual(self.item.status, "Healthy")
        self.resp = self.client.put(
            path=self.item.get_absolute_url(),
            data=JobSerializer(Job(name=self.item.name, status="Degraded")).data,
            content_type="application/json",
        )
        self.item.refresh_from_db()
        self.assertEqual(self.resp.status_code, 200)
        self.assertEqual(self.item.status, "Degraded")
