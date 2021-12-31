from django.views import generic

from features.models import Feature


class FeatureListView(generic.ListView):
    context_object_name = "items"
    model = Feature
    order = ["-created_at"]
    queryset = Feature.objects.all()
    paginate_by = 100

    def get_queryset(self):
        query = super().get_queryset()
        query = query.order_by(*self.order)
        return query

    def get_context_data(self, *args, object_list=None, **kwargs):
        context = super().get_context_data(
            *args, object_list=self.get_queryset(), **kwargs
        )
        context["features"] = {f.name: f.active for f in context.get("items", [])}
        return context
