from django.contrib.auth import mixins as auth
from django.views import generic

from scrutiny.views import ScrutinyListView

from .models import Project


class GraftIndexView(auth.LoginRequiredMixin, generic.TemplateView):
    template_name = "notes/index.html"


class GraftListView(auth.LoginRequiredMixin, ScrutinyListView):
    model = Project
    template_name = "notes/list.html"
