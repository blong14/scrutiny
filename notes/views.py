from io import StringIO
from typing import Dict, List

from django.contrib.auth import mixins as auth
from django.views import generic
import matplotlib.pyplot as plt

from .models import Note, Project


class ProjectIndexView(auth.LoginRequiredMixin, generic.TemplateView):
    template_name = "notes/index.html"


class ProjectDashboardView(auth.LoginRequiredMixin, generic.TemplateView):
    template_name = "notes/dashboard.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)  # noqa
        context["total_projects"] = Project.objects.count()  # noqa
        context["total_notes"] = Note.objects.count()  # noqa
        return context


class ProjectListView(auth.LoginRequiredMixin, generic.ListView):
    context_object_name = "items"
    model = Project
    order = ["-created_at"]
    paginate_by = 10
    template_name = "notes/list.html"

    def get_queryset(self):
        query = super().get_queryset()
        return query.filter(user=self.request.user)


class ProjectDetailView(auth.LoginRequiredMixin, generic.DetailView):
    context_object_name = "item"
    model = Project
    template_name = "notes/detail.html"

    def get_queryset(self):
        query = super().get_queryset()
        return query.prefetch_related("notes").filter(user=self.request.user)

    def get_svg(self, positions: List[Dict[str, float]]) -> str:
        svg = StringIO()
        fig = plt.figure()
        plt.scatter([p["x"] for p in positions if p], [p["y"] for p in positions if p])
        fig.savefig(svg, format="svg")
        svg.seek(0)
        return svg.getvalue()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        positions = [note.position for note in context["item"].notes.all()]
        context["svg"] = self.get_svg(list(positions))
        return context
