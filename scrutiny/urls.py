from django.contrib import admin
from django.urls import path

from jobs.views import JobsApiUpdateView, JobsStatusView
from library.views import PocketListView
from news.views import NewsApiDashboardView, NewsApiListView, NewsListView
from notes.views import GraftListView
from scrutiny.views import ScrutinyAboutView, ScrutinyIndexView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", ScrutinyIndexView.as_view(), name="scrutiny.index"),
    path("about/", ScrutinyAboutView.as_view(), name="scrutiny.about"),
    path("news/", NewsListView.as_view(), name="news.list_view"),
    path("library/", PocketListView.as_view(), name="library.list_view"),
    path("notes/", GraftListView.as_view(), name="notes.list_view"),
    path("api/jobs/status/", JobsStatusView.as_view(), name="jobs_api.dashboard"),
    path(
        "api/jobs/<slug:name>/",
        JobsApiUpdateView.as_view(),
        name="jobs_api.update_view",
    ),
    path("api/news/", NewsApiListView.as_view(), name="news_api.list_view"),
    path(
        "api/news/dashboard/", NewsApiDashboardView.as_view(), name="news_api.dashboard"
    ),
]
