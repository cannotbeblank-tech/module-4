from __future__ import annotations

import random
from dataclasses import dataclass

from faker import Faker

faker = Faker("ru_RU")


@dataclass(frozen=True)
class DataGenerator:

    @staticmethod
    def generate_movie_data(
        *,
        location: str | None = None,
        genre_id: int = 1,
        published: bool = True,
    ) -> dict:
        return {
            "name": f"API movie {faker.uuid4()}",
            "imageUrl": "https://example.com/image.png",
            "price": random.randint(100, 1000),
            "description": faker.text(max_nb_chars=100),
            "location": location or random.choice(["SPB", "MSK"]),
            "published": published,
            "genreId": genre_id,
        }

    @staticmethod
    def generate_invalid_movie_data() -> dict:
        return {
            "name": f"Invalid movie {faker.uuid4()}",
            "imageUrl": "not-a-valid-url",
            "price": 0,
            "description": "",
            "location": "INVALID",
            "published": True,
            "genreId": 0,
        }
