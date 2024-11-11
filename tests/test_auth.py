import sys
import os
import pytest
from fastapi.testclient import TestClient
from main import app
from app.db import crud
from app.api.user import oauth2_scheme
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock
from passlib.context import CryptContext

import jwt
from _datetime import datetime, timedelta
from app.core.config import settings


def generate_test_token():
    secret_key = settings.JWT_SECRET_KEY
    algorithm = settings.JWT_ALGORITHM
    expire = datetime.utcnow() + timedelta(seconds=settings.JWT_EXPIRATION_TIME)

    payload = {
        "sub": "validuser",  # Вместо "id" используем "sub" для имени пользователя
        "exp": expire
    }

    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token


# Инициализация контекста для Passlib
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_get_db(mocker):
    # Мокируем зависимость get_db, чтобы не использовать реальную базу данных
    db = AsyncMock(spec=AsyncSession)
    db_user = MagicMock()
    db_user.id = 1
    db_user.username = "validuser"
    mocker.patch("app.db.crud.get_user_by_username", return_value=db_user)
    return db


@pytest.fixture
def valid_token():
    """Фикстура для генерации токена для авторизованных запросов"""
    return generate_test_token()


@pytest.mark.asyncio
async def test_register_user(client, mock_get_db, valid_token):
    # Тест на успешную регистрацию нового пользователя
    mock_get_db.return_value = AsyncMock()
    user_data = {
        "username": "newuser",
        "password": "newpassword"
    }

    crud.get_user_by_username = AsyncMock(return_value=None)

    created_user = {
        "id": 1,
        "username": "newuser",
    }

    crud.create_user = AsyncMock(return_value=created_user)

    response = client.post("/register", json=user_data)

    assert response.status_code == 200
    assert response.json() == created_user


@pytest.mark.asyncio
async def test_register_user_existing_username(client, mock_get_db, valid_token):
    # Тест на попытку регистрации с уже существующим именем пользователя
    mock_get_db.return_value = AsyncMock()
    user_data = {
        "username": "existinguser",
        "password": "password"
    }

    crud.get_user_by_username = AsyncMock(return_value=user_data)

    response = client.post("/register", json=user_data)

    assert response.status_code == 400
    assert response.json() == {"detail": "Username already registered"}


@pytest.mark.asyncio
async def test_login_user(client, mock_get_db, mocker, valid_token):
    # Тест на успешный вход
    user_data = {
        "username": "validuser",
        "password": "validpassword"
    }

    hashed_password = pwd_context.hash("validpassword")

    db_user = MagicMock()
    db_user.username = "validuser"
    db_user.hashed_password = hashed_password
    db_user.id = 1
    crud.get_user_by_username = AsyncMock(return_value=db_user)

    mocker.patch("app.core.security.verify_password", return_value=True)

    response = client.post("/login", json=user_data)

    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_invalid_credentials(client, mock_get_db, valid_token):
    # Тест на невалидные данные для входа
    user_data = {
        "username": "invaliduser",
        "password": "wrongpassword"
    }

    crud.get_user_by_username = AsyncMock(return_value=None)

    response = client.post("/login", json=user_data)

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


@pytest.mark.asyncio
async def test_get_user_profile_valid_token(client, mock_get_db, valid_token):
    # Тест с валидным токеном
    response = client.get("/profile", headers={"Authorization": f"Bearer {valid_token}"})

    assert response.status_code == 200
    assert response.json() == {"id": 1, "username": "validuser"}  # Пример ответа


@pytest.mark.asyncio
async def test_get_user_profile_invalid_token(client, mock_get_db, valid_token):
    # Тест на невалидный токен
    invalid_token = "invalid_token"  # Просто подставим строку вместо сгенерированного токена

    response = client.get("/profile", headers={"Authorization": f"Bearer {invalid_token}"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}
