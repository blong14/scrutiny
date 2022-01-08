from django.views import generic
from opentelemetry import trace

from features.models import Feature


tracer = trace.get_tracer(__name__)


class FeatureListView(generic.ListView):
    context_object_name = "items"
    model = Feature
    module = "features.views.FeatureListView"
    order = ["-created_at"]
    queryset = Feature.objects.all()
    paginate_by = 100

    def get_queryset(self):
        query = super().get_queryset()
        query = query.order_by(*self.order)
        return query

    def get_context_data(self, *args, object_list=None, **kwargs):
        with tracer.start_as_current_span(f"{self.module}.get_context_data"):
            context = super().get_context_data(
                *args, object_list=self.get_queryset(), **kwargs
            )
            context["features"] = {f.name: f.active for f in context.get("items", [])}
            return context
