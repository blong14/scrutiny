from typing import List

from django.test import Client
from django.urls import reverse

from notes.models import Project
from scrutiny.tests import ScrutinyTestListView


def project(*args, **kwargs) -> Project:
    pr = Project(
        project_id=123,
        *args,
        **kwargs,
    )
    pr.save()
    return pr


class TestListView(ScrutinyTestListView):
    client_class = Client

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("notes.list_view")
        self.items: List[Project] = [
            project(title="project_1"),
            project(title="project_2"),
        ]

    def tearDown(self) -> None:
        super().tearDown()
        Project.objects.all().delete()

    def test_no_items(self) -> None:
        self.tearDown()
        super().test_no_items()

    def test_items(self) -> None:
        super().test_items()
        self.assertListResponseContains([item.title for item in self.items])
