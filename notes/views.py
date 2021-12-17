from scrutiny.views import ScrutinyListView

from .models import Project


class GraftListView(ScrutinyListView):
    model = Project
    template_name = "notes/list.html"
