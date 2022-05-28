from typing import Any, Dict, List

from django.contrib.auth import mixins as auth
from django.views import generic
from django.template.loader import render_to_string

from .models import Note, Project
from .services import DirectedGraph
from .signals import send


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
    graph = DirectedGraph
    model = Project
    order = ["-created_at"]
    paginate_by = 10
    template_name = "notes/list.html"

    def get_queryset(self):
        query = super().get_queryset()
        return query.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not len(context["items"]):
            return context
        context["graph"] = self.graph(
            **ProjectDetailView.get_graph_data(
                context[self.context_object_name][0].notes.all()
            ),
        ).getvalue()
        return context


class ProjectDetailView(auth.LoginRequiredMixin, generic.DetailView):
    context_object_name = "item"
    graph = DirectedGraph
    model = Project
    template_name = "notes/detail.html"

    @staticmethod
    def get_graph_data(notes: List[Note]) -> Dict[str, List[Any]]:
        nodes = [
            (
                note.slug,
                {
                    "pos": (note.position["x"], note.position["y"] * -1)
                    if note.position
                    else (0, 0)
                },
            )
            for note in notes
        ]
        edges = [
            (note.slug, neighbor["note_id"])
            for note in notes
            if note.neighbors
            for neighbor in note.neighbors
        ]
        return dict(nodes=nodes, edges=edges)

    def get_queryset(self):
        query = super().get_queryset()
        return query.prefetch_related("notes").filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["graph"] = self.graph(
            **self.get_graph_data(context[self.context_object_name].notes.all()),
        ).getvalue()
        return context


class ProjectAnimateGraphView(auth.LoginRequiredMixin, generic.DetailView):
    context_object_name = "item"
    graph = DirectedGraph
    model = Project
    template_name = "notes/graph.html"

    def get_queryset(self):
        query = super().get_queryset()
        return query.prefetch_related("notes").filter(user=self.request.user)

    def render_svgs(self, notes: List[Note]):
        all_nodes, all_edges = [], []
        graph_data = ProjectDetailView.get_graph_data(notes)
        for edge in graph_data.get("edges"):
            all_edges.append(edge)
            for node in graph_data.get("nodes"):
                if node[0] in edge:
                    all_nodes.append(node)
            yield self.graph(nodes=all_nodes, edges=all_edges).getvalue()

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        last_svg = None
        for svg in self.render_svgs(context[self.context_object_name].notes.all()):
            msg = render_to_string("notes/_graph.html", context=dict(frame=svg))
            send(msg)
            last_svg = svg
        context["frame"] = last_svg
        return context
