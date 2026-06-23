from locust import HttpUser, task, between

class BienestarUser(HttpUser):
    # Simula una espera de entre 1 y 5 segundos entre peticiones
    wait_time = between (1,5)

    @task
    def test_home(self):
        #Cambia esto por una ruta valida de tu backend/Api (ej: /api/loands o /)
        self.client.get("/")