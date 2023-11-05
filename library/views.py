from django.contrib.auth import mixins as auth
from django.db.models import Q
from django.views import generic

from .models import Article, Tag


class IndexView(auth.LoginRequiredMixin, generic.TemplateView):
    template_name = "library/index.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        return context


class TagListView(auth.LoginRequiredMixin, generic.ListView):
    context_object_name = "items"
    model = Tag
    order = ["value"]
    template_name = "library/tags/list.html"

    def get_queryset(self, *args, **kwargs):
        return self.model.objects.filter(user=self.request.user).order_by(*self.order)


class ArticleListView(auth.LoginRequiredMixin, generic.ListView):
    context_object_name = "items"
    model = Article
    order = ["-created_at"]
    page_kwarg = "page"
    paginate_by = 10
    template_name = "library/articles/list.html"

    def get_context_data(self, *args, object_list=None, **kwargs):
        context = super().get_context_data(*args, object_list=object_list, **kwargs)
        context.pop("object_list")
        context["source_url"] = "library.list_view"
        context["tag"] = self.request.GET.get("tag")
        context["search"] = self.request.GET.get("search")
        return context

    def get_queryset(self):
        query = super().get_queryset()
        query = (
            query.prefetch_related("tags")
            .filter(user=self.request.user)
            .order_by(*self.order)
        )
        tag = self.request.GET.get("tag")
        if tag:
            query = query.filter(tags__value=tag)
        search = self.request.GET.get("search")
        if search:
            query = query.filter(
                Q(resolved_title__contains=search)
                | Q(excerpt__contains=search)
                | Q(tags__value=search)
            ).distinct()
        return query
