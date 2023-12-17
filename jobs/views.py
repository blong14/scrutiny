import json
from http import HTTPStatus

from django.contrib.auth import mixins as auth
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy

from .apps import publisher
from .forms import JobForm
from .models import Job


class JobListView(auth.LoginRequiredMixin, ListView):
    model = Job
    paginate_by = 10
    template_name = "jobs/job_list.html"

    def get(self, request, *args, **kwargs):
        resp = super().get(request, *args, **kwargs)
        if publisher and resp.status_code < HTTPStatus.BAD_REQUEST:
            publisher.publish(json.dumps({"topic": "news-summary", "action": "start"}))
        return resp


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
