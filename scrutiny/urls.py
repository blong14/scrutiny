from django.contrib import admin
from django.urls import include, path

from library.views import IndexView as LibraryView, ArticleListView, TagListView
from news.views import (
    IndexView as NewsView,
    NewsListView,
    NewsItemFormView,
)
from jobs.views import JobListView, JobDetailView, JobCreateView, JobUpdateView

from .views import ScrutinyAboutView, ScrutinyIndexView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("django.contrib.auth.urls")),
    path("", include("social_django.urls", namespace="social")),
    path("", ScrutinyIndexView.as_view(), name="index"),
    path("about/", ScrutinyAboutView.as_view(), name="about"),
    path("news/", NewsView.as_view(), name="news"),
    path("news/feeds/", NewsListView.as_view(), name="news.feed_view"),
    path("news/save/", NewsItemFormView.as_view(), name="news.save_view"),
    path("library/", LibraryView.as_view(), name="library"),
    path("library/list/", ArticleListView.as_view(), name="library.list_view"),
    path("library/tags/", TagListView.as_view(), name="library.tag_view"),
    path("jobs/", JobListView.as_view(), name="jobs"),
    path("jobs/<int:pk>/", JobDetailView.as_view(), name="job_detail"),
    path("jobs/create/", JobCreateView.as_view(), name="job_create"),
    path("jobs/<int:pk>/update/", JobUpdateView.as_view(), name="job_update"),
]
