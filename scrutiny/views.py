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
    order = ["-time"]
    paginate_by = 10

    def get_queryset(self):
        query = self.model.objects.all()
        slugs = self.request.GET.get("slugs")
        if slugs:
            query = query.filter(pk__in=[slug for slug in slugs.split(",")])
        return query


class ScrutinyDetailView(generic.DetailView):
    context_object_name = "item"


class ScrutinyTemplateView(generic.TemplateView):
    pass
