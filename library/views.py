import logging
from datetime import datetime

from django.contrib.auth import mixins as auth
from django.db.models import Q
from django.forms import Form
from django.views import generic

from library.models import Article, Tag
from library.client import HttpRequest, PocketClient
from scrutiny.env import get_pocket_consumer_key


class IndexView(auth.LoginRequiredMixin, generic.TemplateView):
    template_name = "library/index.html"


class TagListView(auth.LoginRequiredMixin, generic.ListView):
    context_object_name = "items"
    model = Tag
    order = ["value"]
    template_name = "library/tags.html"

    def get_queryset(self, *args, **kwargs):
        return self.model.objects.filter(user=self.request.user).order_by(*self.order)


class ArticleListView(auth.LoginRequiredMixin, generic.ListView):
    context_object_name = "items"
    model = Article
    order = ["-created_at"]
    page_kwarg = "page"
    paginate_by = 10
    template_name = "library/list.html"

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
            )
        return query


class ArticleForm(Form):
    client = PocketClient

    class Meta:
        fields = ["url"]

    def add(self, request):
        import urllib.parse

        resp = self.client().add(
            HttpRequest(
                data=dict(
                    url=urllib.parse.quote(self.data["url"], safe=""),
                    time=int(datetime.utcnow().timestamp()),
                    consumer_key=get_pocket_consumer_key(),
                    access_token=request.user.social_auth.first().extra_data.get(
                        "access_token", ""
                    ),
                ),
            )
        )
        try:
            import pdb

            pdb.set_trace()
            article = Article(**resp.data)
            article.save()
        except Exception as e:
            logging.error(e)


class ArticleFormView(generic.FormView):
    success_url = "library.list_view"
    form_class = ArticleForm

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            form.add(request)
            return self.form_valid(form, **kwargs)
        else:
            return self.form_invalid(form, **kwargs)

    def form_valid(self, form, **kwargs):
        context = self.get_context_data(**kwargs)
        context.update(
            {
                "form": form,
            }
        )
