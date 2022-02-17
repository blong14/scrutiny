from django.contrib.auth import mixins as auth
from django.views import generic

from library.models import Article, Tag


class IndexView(auth.LoginRequiredMixin, generic.TemplateView):
    template_name = "library/index.html"


class TagListView(auth.LoginRequiredMixin, generic.ListView):
    context_object_name = "items"
    model = Tag
    template_name = "library/tags.html"

    def get_queryset(self, *args, **kwargs):
        return self.model.objects.filter(user=self.request.user).all()


class PocketListView(generic.ListView):
    context_object_name = "items"
    model = Article
    order = ["-created_at"]
    page_kwarg = "page"
    paginate_by = 10
    template_name = "library/list.html"

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user).order_by(
            *self.order
        )
