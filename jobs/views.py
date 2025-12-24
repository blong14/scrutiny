import json
import logging
from http import HTTPStatus

import pika
from django.contrib import messages

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


class JobDetailView(auth.LoginRequiredMixin, DetailView):
    model = Job
    slug_field = "name"
    template_name = "jobs/job_detail.html"

    def get_object(self, queryset=None):
        return super().get_object(queryset=queryset)


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
