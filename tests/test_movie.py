import sys
import os
from unittest import mock
import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch
import jwt
from _datetime import datetime, timedelta
from app.core.config import settings


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


client = TestClient(app)


@pytest.fixture
def generate_test_token():
    secret_key = settings.JWT_SECRET_KEY
    algorithm = settings.JWT_ALGORITHM
    expire = datetime.utcnow() + timedelta(seconds=settings.JWT_EXPIRATION_TIME)

    payload = {
        "id": 1,
        "exp": expire
    }

    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    print(token)
    return token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_movie_data():
    return {
        "filmId": 1,
        "nameRu": "Тестовый фильм",
        "year": "2024",
        "description": "Описание тестового фильма",
        "rating": "8.5"
    }


@pytest.fixture
def search_movies_data():
    return {
        'films': [
            {
                'filmId': 1,
                'nameRu': 'Тестовый фильм',
                'year': 2023,
                'description': 'Описание тестового фильма',
                'rating': '8.5',
            }
        ]
    }


@pytest.fixture
def mock_movie_details():
    return {
        "kinopoiskId": 1,
        "nameRu": "Тестовый фильм",
        "year": 2024,
        "description": "Описание тестового фильма",
        "rating": 8.5,
        "genres": [{"genre": "Drama"}],
        "countries": [{"country": "Russia"}],
        "director": "John Doe",
        "actors": ["Actor1", "Actor2"],
        "duration": 120,
        "posterUrl": "https://example.com/poster.jpg"
    }


@pytest.fixture
def mock_favorite_data():
    """Фикстура с данными для избранного."""
    return {
        "kinopoisk_id": 1,
        "title": "Тестовый фильм",
        "year": 2024
    }


@pytest.fixture
def mock_get_favorites_by_user():
    with mock.patch("app.db.crud.get_favorites_by_user") as mock_get:
        yield mock_get


@patch("app.api.movie.get_kinopoisk_data")
def test_search_movies(mock_get_kinopoisk_data, client, generate_test_token, search_movies_data):
    """Тест поиска фильмов по запросу."""

    mock_get_kinopoisk_data.return_value = search_movies_data

    query = "Тестовый фильм"

    response = client.get("/search",
                          params={"query": query},
                          headers={"Authorization": f"Bearer {generate_test_token}"})

    assert response.status_code == 200

    response_data = response.json()

    assert len(response_data) == 1
    assert response_data[0]["kinopoisk_id"] == 1
    assert response_data[0]["title"] == "Тестовый фильм"
    assert response_data[0]["year"] == 2023
    assert response_data[0]["description"] == "Описание тестового фильма"
    assert response_data[0]["rating"] == 8.5


@patch("app.api.movie.get_kinopoisk_data")
def test_search_movies_no_results(mock_get_kinopoisk_data, generate_test_token, client):
    """Тест, если фильмы не найдены."""

    mock_get_kinopoisk_data.return_value = {"films": []}

    response = client.get("/search", params={"query": "Неизвестный фильм"},
                          headers={"Authorization": f"Bearer {generate_test_token}"})

    assert response.status_code == 200
    assert response.json() == []


@patch("app.api.movie.get_kinopoisk_data")
def test_get_movie_details(mock_get_kinopoisk_data, generate_test_token, mock_movie_details, client):
    """Тест получения подробной информации о фильме."""
    mock_get_kinopoisk_data.return_value = mock_movie_details

    response = client.get("/movies/1", headers={"Authorization": f"Bearer {generate_test_token}"})

    assert response.status_code == 200
    assert response.json()["kinopoisk_id"] == mock_movie_details["kinopoiskId"]
    assert response.json()["title"] == mock_movie_details["nameRu"]


@patch("app.api.movie.get_kinopoisk_data")
def test_get_movie_details_not_found(mock_get_kinopoisk_data, generate_test_token, client):
    """Тест, если фильм не найден."""
    mock_get_kinopoisk_data.return_value = None

    response = client.get("/movies/9999", headers={"Authorization": f"Bearer {generate_test_token}"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Film not found"


@patch("app.db.crud.get_favorites_by_user")
def test_add_to_favorites_already_exists(mock_get_favorites_by_user, generate_test_token, mock_favorite_data, client):
    """Тест, если фильм уже есть в избранном."""
    mock_get_favorites_by_user.return_value = mock_favorite_data

    response = client.post("/movies/favorites", json=mock_favorite_data,
                           headers={"Authorization": f"Bearer {generate_test_token}"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Movie already in favorites"


@patch("app.db.crud.get_favorites_by_user")
def test_remove_from_favorites_not_found(mock_get_favorites_by_user, generate_test_token, mock_favorite_data, client):
    """Тест, если фильм не найден в избранном."""
    mock_get_favorites_by_user.return_value = None

    response = client.delete(f"/favorites/{mock_favorite_data['kinopoisk_id']}",
                             headers={"Authorization": f"Bearer {generate_test_token}"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Not Found"
