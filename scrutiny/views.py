from django.conf import settings
from django.views import generic
from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response


class ScrutinyApiListView(ListCreateAPIView):
    def create(self, request, *args, **kwargs):
        many = True if isinstance(request.data, list) else False
        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)


class ScrutinyListView(generic.ListView):
    context_object_name = "items"
    paginate_by = 10

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["features"] = getattr(settings, "FEATURES", {})
        return context


class ScrutinyDetailView(generic.DetailView):
    context_object_name = "item"


class ScrutinyIndexView(generic.TemplateView):
    template_name = "index.html"
