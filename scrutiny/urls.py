from django.contrib import admin
from django.urls import include, path

from jobs.views import JobsApiUpdateView, JobsStatusView
from library.views import IndexView, PocketListView
from news.views import NewsApiDashboardView, NewsApiListView, NewsListView
from notes.views import GraftApiDashboardView, GraftListView
from scrutiny.views import ScrutinyAboutView, ScrutinyIndexView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("django.contrib.auth.urls")),
    path("", include("social_django.urls", namespace="social")),
    path("", ScrutinyIndexView.as_view(), name="scrutiny.index"),
    path("about/", ScrutinyAboutView.as_view(), name="scrutiny.about"),
    path("news/", NewsListView.as_view(), name="news.list_view"),
    path("library/", IndexView.as_view(), name="library.index_view"),
    path("library/list/", PocketListView.as_view(), name="library.list_view"),
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
    path(
        "api/notes/dashboard/",
        GraftApiDashboardView.as_view(),
        name="notes_api.dashboard",
    ),
]
