from django.shortcuts import get_object_or_404
from django.views import generic
from rest_framework.generics import UpdateAPIView

from jobs.models import Job
from jobs.serializers import JobSerializer


class JobsStatusView(generic.TemplateView):
    model = Job
    module = "jobs.views.JobsStatusView"
    template_name = "jobs/dashboard.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        name = self.request.GET.get("name") if self.request else None
        if not name:
            name = kwargs.pop("name")
        item = get_object_or_404(self.model, name=name)
        context["status"] = item.status if item.active else "Degraded"
        context["last_sync"] = item.synced_at
        return context


class JobsApiUpdateView(UpdateAPIView):
    lookup_field = "name"
    queryset = Job.objects.all()
    serializer_class = JobSerializer
