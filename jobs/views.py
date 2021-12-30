from django.shortcuts import get_object_or_404
from django.views import generic

from jobs.models import Job


class JobsStatusView(generic.TemplateView):
    model = Job
    template_name = "jobs/status.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        name = self.request.GET.get("name") if self.request else None
        item = get_object_or_404(self.model, name=name)
        context["last_sync"] = item.synced_at
        return context
