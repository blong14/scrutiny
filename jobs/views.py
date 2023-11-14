from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy

from .forms import JobForm
from .models import Job


class JobListView(ListView):
    model = Job
    template_name = "jobs/job_list.html"


class JobDetailView(DetailView):
    model = Job
    template_name = "jobs/job_detail.html"


class JobCreateView(CreateView):
    model = Job
    form_class = JobForm
    template_name = "jobs/job_form.html"
    success_url = reverse_lazy("job_list")


class JobUpdateView(UpdateView):
    model = Job
    form_class = JobForm
    template_name = "jobs/job_form.html"
    success_url = reverse_lazy("job_list")
