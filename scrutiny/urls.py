from django.contrib import admin
from django.urls import include, path

from library.views import IndexView as LibraryView, ArticleListView, TagListView
from news.views import IndexView as NewsView, NewsListView
from notes.views import (
    ProjectDashboardView,
    ProjectDetailView,
    ProjectAnimateGraphView,
    ProjectIndexView,
    ProjectListView,
)
from .views import ScrutinyAboutView, ScrutinyIndexView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("django.contrib.auth.urls")),
    path("", include("social_django.urls", namespace="social")),
    path("", ScrutinyIndexView.as_view(), name="scrutiny.index"),
    path("about/", ScrutinyAboutView.as_view(), name="scrutiny.about"),
    path("news/", NewsView.as_view(), name="news.list_view"),
    path("news/feeds/", NewsListView.as_view(), name="news.feed_view"),
    path("library/", LibraryView.as_view(), name="library.index_view"),
    path("library/list/", ArticleListView.as_view(), name="library.list_view"),
    path("library/save/", ArticleListView.as_view(), name="library.save_view"),
    path("library/tags/", TagListView.as_view(), name="library.tag_view"),
    path("notes/", ProjectIndexView.as_view(), name="notes.index_view"),
    path("notes/list/", ProjectListView.as_view(), name="notes.list_view"),
    path(
        "notes/detail/<slug:slug>/",
        ProjectDetailView.as_view(),
        name="notes.detail_view",
    ),
    path(
        "notes/animate/<slug:slug>/",
        ProjectAnimateGraphView.as_view(),
        name="notes.graph_animation_view",
    ),
    path(
        "api/notes/dashboard/",
        ProjectDashboardView.as_view(),
        name="notes_api.dashboard",
    ),
]
