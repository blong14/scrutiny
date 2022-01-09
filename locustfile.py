from locust import HttpUser, task


class User(HttpUser):
    def on_start(self):
        """on_start is called when a Locust start before any task is scheduled"""
        self.client.verify = False

    @task
    def index(self):
        self.client.get("/")


class About(User):
    @task
    def about(self):
        self.client.get("/about/")


class News(User):
    @task
    def news(self):
        self.client.get("/news/")


class Notes(User):
    @task
    def notes(self):
        self.client.get("/notes/")


class Library(User):
    @task
    def library(self):
        self.client.get("/library/")


class ApiNews(User):
    @task
    def news(self):
        self.client.get("/api/news/")


class ApiNewsDashboard(User):
    @task
    def dashboard(self):
        self.client.get("/api/news/dashboard/")


class ApiJobStatus(User):
    @task
    def status(self):
        self.client.get("/api/jobs/status/?hackernews")
