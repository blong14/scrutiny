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
