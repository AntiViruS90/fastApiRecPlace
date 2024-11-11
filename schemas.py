from pydantic import BaseModel
from typing import List, Optional


# Схема для регистрации нового пользователя
class UserCreate(BaseModel):
    username: str
    password: str


# Схема для отображения информации о пользователе
class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


# Схема для ответа с токеном JWT
class Token(BaseModel):
    access_token: str
    token_type: str


# Схема для поиска фильмов
class MovieSearchResult(BaseModel):
    kinopoisk_id: int
    title: str
    year: Optional[int] = None
    description: Optional[str] = None
    rating: Optional[float] = None
    poster_url: Optional[str] = None

    class Config:
        from_attributes = True


# Схема для фильма (поиск фильма)
class Movie(BaseModel):
    kinopoisk_id: int
    title: str
    year: Optional[int] = None
    description: Optional[str] = None
    rating: Optional[float] = None
    poster_url: Optional[str] = None

    class Config:
        from_attributes = True


# Схема для детальной информации о фильме
class MovieDetail(MovieSearchResult):
    countries: List[str]
    genres: List[str]
    director: Optional[str] = None
    actors: Optional[List[str]] = []
    duration: Optional[int] = None  # продолжительность в минутах
    poster_url: Optional[str] = None  # ссылка на постер

    class Config:
        from_attributes = True


# Схема для добавления фильма в избранное
class FavoriteCreate(BaseModel):
    kinopoisk_id: int
    title: str
    year: int

    class Config:
        from_attributes = True


# Схема для вывода фильма из избранного
class FavoriteOut(BaseModel):
    kinopoisk_id: int
    title: str
    year: int

    class Config:
        from_attributes = True
