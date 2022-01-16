from django.contrib.auth import mixins as auth

from scrutiny.views import ScrutinyListView

from .models import Project


class GraftListView(auth.LoginRequiredMixin, ScrutinyListView):
    model = Project
    template_name = "notes/list.html"
