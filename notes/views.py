from django.contrib.auth import mixins as auth
from django.views import generic
from opentelemetry import trace

from scrutiny.views import ScrutinyListView

from .models import Note, Project


tracer = trace.get_tracer(__name__)


class GraftApiDashboardView(auth.LoginRequiredMixin, generic.TemplateView):
    template_name = "notes/dashboard.html"
    module = f"{__name__}.NewsApiDashboardView"

    def get_context_data(self, *args, **kwargs):
        with tracer.start_as_current_span(f"{self.module}.get_context_data"):
            context = super().get_context_data(*args, **kwargs)
            with tracer.start_as_current_span(f"{self.module}.Items.total_projects"):
                context["total_projects"] = Project.objects.count()
            with tracer.start_as_current_span(f"{self.module}.Items.total_notes"):
                context["total_notes"] = Note.objects.count()
            return context


class GraftListView(auth.LoginRequiredMixin, ScrutinyListView):
    context_object_name = "items"
    model = Project
    module = f"{__name__}.GraftListView"
    paginate_by = 10
    order = ["-created_at"]
    template_name = "notes/list.html"

    def get_queryset(self):
        with tracer.start_as_current_span(f"{self.module}.get_query_set"):
            query = self.model.objects.prefetch_related("notes")
            slugs = self.request.GET.get("slugs") if self.request else None
            if slugs:
                query = query.filter(slug__in=[slug for slug in slugs.split(",")])
            query = query.order_by(*self.order)
            return query
