from django.contrib.auth import mixins as auth

from library.models import Article
from scrutiny.views import ScrutinyListView


class PocketListView(auth.LoginRequiredMixin, ScrutinyListView):
    model = Article
    template_name = "library/list.html"
