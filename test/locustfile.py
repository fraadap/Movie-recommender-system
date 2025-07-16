from locust import HttpUser, task, between
import random
import string

# host locust: https://kzy0xi6gle.execute-api.us-east-1.amazonaws.com/deploy

class MovieUser(HttpUser):

    def on_start(self):
        self.client.post("/")

    wait_time = between(1, 2)
    valid_movie_ids = ["228", "4274", "265330", "79860", "133469"]
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiOWRiN2FmYTItNmJkOC00ZTYwLTk4Y2MtMWQ1ZjYxMDdlOTQ5IiwiZW1haWwiOiJkYXByaWxlLmZyYW5jZXNjbzAyQGdtYWlsLmNvbSIsIm5hbWUiOiJmcmFhLmRhcCIsImlhdCI6MTc0OTEzMTUwNywiZXhwIjoxMTc0OTEzMTUwNn0.gmnOqH-cm-0BXmmGYG97B0X80AlThniWV-pa5hdvXvE"


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

    @task(1)
    def search(self):
        query = random.choice(self.search_queries)
        self.client.post(
            "/search",
            json={
                "query": query,
                "top_k": 10
            }
        )

    @task(1)
    def content_based(self):
        movie_ids = [[mid, 5.0] for mid in random.sample(self.valid_movie_ids, 3)]
        self.client.post("/content", json={
            "movie_ids": movie_ids,
            "top_k": 10
        })

    @task(1)
    def similar_movies(self):
        movie_id = random.choice(self.valid_movie_ids)
        self.client.post("/similar", json={
            "movie_id": movie_id,
            "top_k": 10
        })

    @task(1)
    def collaborative(self):
        response = self.client.post("/collaborative", headers={
            "Authorization": f"Bearer {self.token}"
        }, json={"top_k": 10})
    