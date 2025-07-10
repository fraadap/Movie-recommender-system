from locust import HttpUser, task, between
import random
import string

# host locust: https://kzy0xi6gle.execute-api.us-east-1.amazonaws.com/deploy

class MovieUser(HttpUser):
    wait_time = between(1, 2)

    search_queries = [
        "action movies with superheroes and adventure",
        "romantic comedies set in New York",
        "sci-fi movies about space exploration",
        "animated family movies",
        "thrillers with plot twists",
        "classic western films",
        "horror movies with haunted houses",
        "biographical sports dramas",
        "fantasy movies with dragons",
        "crime movies based on true stories"
    ]

    @task(2)
    def register(self):
        email = "testuser_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)) + "@example.com"
        self.client.post("/auth/register", json={
            "name": "Test User",
            "email": email,
            "password": "TestPassword123!"
        })

    @task(3)
    def search(self):
        query = random.choice(self.search_queries)
        self.client.post(
            "/search",
            json={
                "query": query,
                "top_k": 10
            }
        )