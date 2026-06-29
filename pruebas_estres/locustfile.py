from locust import HttpUser, task, between

class BienestarMindUser(HttpUser):

    wait_time = between(1, 2)

    @task(5)
    def inicio(self):
        self.client.get("/inicio/")

    @task(3)
    def login(self):
        self.client.get("/login/")

    @task(1)
    def home(self):
        self.client.get("/")