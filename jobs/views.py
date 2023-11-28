import json

import pika
from pika.exchange_type import ExchangeType
from django.contrib.auth import mixins as auth
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy

from scrutiny.env import (
    get_mercure_sub_token,
    get_mercure_url,
    get_rmq_dsn,
)
from .forms import JobForm
from .models import Job


class Publisher:
    def __init__(self, topic: str):
        params = pika.URLParameters(get_rmq_dsn())
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()
        self.channel.exchange_declare("news", exchange_type=ExchangeType.direct)
        self.channel.queue_declare(queue=topic)

    def publish(self, topic: str):
        self.channel.basic_publish(
            exchange="news",
            routing_key=topic,
            body=json.dumps({"topic": topic, "action": "start"}).encode(),
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
        self.publisher(topic=self.topic).publish(topic=self.topic)
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
