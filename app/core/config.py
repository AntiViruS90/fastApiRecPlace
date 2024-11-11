import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_TIME = 72000  # 1 hour
    KINOPOISK_API_KEY = os.getenv("KINOPOISK_API_KEY")


settings = Settings()
