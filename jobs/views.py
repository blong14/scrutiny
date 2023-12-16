from django.contrib.auth import mixins as auth
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy

from .apps import broadcast
from .forms import JobForm
from .models import Job


class JobListView(auth.LoginRequiredMixin, ListView):
    model = Job
    paginate_by = 10
    template_name = "jobs/job_list.html"

    @broadcast(topic="news-summary", msg={"topic": "news-summary", "action": "start"})
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class JobDetailView(auth.LoginRequiredMixin, DetailView):
    model = Job
    template_name = "jobs/job_detail.html"


class JobCreateView(auth.LoginRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = "jobs/job_form.html"
    success_url = reverse_lazy("job_list")


class JobUpdateView(auth.LoginRequiredMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = "jobs/job_form.html"
    success_url = reverse_lazy("job_list")
