import logging
import functools

import pika
from django.contrib.auth import mixins as auth
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy

from scrutiny.env import get_mercure_sub_token, get_mercure_url  # noqa
from .forms import JobForm
from .models import Job


class Publisher:
    def __init__(self):
        self.connection = pika.BlockingConnection()
        self.channel = self.connection.channel()

    def publish(self, topic: str):
        self.channel.basic_publish(
            exchange='test',
            routing_key=topic,
            body=b'start',
        )
        self.connection.close()


class JobListView(auth.LoginRequiredMixin, ListView):
    model = Job
    paginate_by = 10
    publisher = Publisher
    template_name = "jobs/job_list.html"
    topic = "news-summary"

    def get_context_data(self, **kwargs):
        mercure_url = get_mercure_url()
        mercure_token = get_mercure_sub_token()
        context = super().get_context_data(**kwargs)
        context.update(
            {"topic": f"{mercure_url}?topic={self.topic}&authorization={mercure_token}"}
        )
        self.publisher().publish(topic=self.topic)
        return context


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
