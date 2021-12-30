from django.contrib import admin
from django.urls import path

from jobs.views import JobsStatusView
from library.views import PocketListView
from news.views import NewsApiDashboardView, NewsApiListView, NewsListView
from notes.views import GraftListView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", NewsListView.as_view(), name="news.index"),
    path("news/", NewsListView.as_view(), name="news.list_view"),
    path("library/", PocketListView.as_view(), name="library.list_view"),
    path("notes/", GraftListView.as_view(), name="notes.list_view"),
    path("api/jobs/status/", JobsStatusView.as_view(), name="jobs_api.status"),
    path("api/news/", NewsApiListView.as_view(), name="news_api.list_view"),
    path(
        "api/news/dashboard/", NewsApiDashboardView.as_view(), name="news_api.dashboard"
    ),
]
