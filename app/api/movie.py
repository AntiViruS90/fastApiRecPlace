import httpx
from fastapi import APIRouter, Depends, HTTPException
from app.core.config import settings
from app.db.session import get_db
from schemas import Movie, MovieDetail, FavoriteCreate, FavoriteOut
from app.api.dependencies import get_current_user
from app.db.crud import (
    get_favorites_by_user,
    get_favorite_with_user_id,
    create_favorite,
    remove_favorite
)
from sqlalchemy.ext.asyncio import AsyncSession
import logging

router = APIRouter()


# Асинхронная функция для получения данных с Kinopoisk API
async def get_kinopoisk_data(endpoint: str, params: dict = None, headers: dict = None):
    """
    Description:
    ------------
        Asynchronous function to perform a GET request to the Kinopoisk API, retrieving movie
        data using the provided endpoint, params, and headers.

    Parameters:
    -----------
        endpoint (str):
            The URL of the API endpoint.
        params (dict, optional):
            A dictionary of parameters to send with the request. Default is None.
        headers (dict, optional):
            A dictionary of headers to send with the request. Default is None.

    Returns:
    --------
        Returns the JSON response from the Kinopoisk API.

    Exceptions:
    -----------
        Raises an HTTPException with status code 500 if the request fails or an error occurs while processing the data.

    Notes:
    ------
         The function logs the request parameters, response status, and content for debugging purposes.
    """
    headers = {
        "X-API-KEY": settings.KINOPOISK_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient() as client:
            # Логируем параметры запроса
            logging.info(f"Requesting URL: {endpoint} with params: {params}")
            response = await client.get(endpoint, params=params, headers=headers)

            # Логируем статус ответа
            logging.info(f"Response status: {response.status_code}")

            if response.status_code != 200:
                logging.error(f"Failed to fetch data: {response.text}")
                raise HTTPException(status_code=500, detail="Failed to fetch data from Kinopoisk API")

            # Логируем содержимое ответа
            logging.info(f"Response content: {response.text}")
            return response.json()
    except Exception as e:
        logging.error(f"Error during API request: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while requesting Kinopoisk API")


# Эндпойнт для поиска фильмов
@router.get("/search", response_model=list[Movie])
async def search_movies(query: str, token: str = Depends(get_current_user)):
    """
    Description:
    -----------
        Endpoint to search for movies by keyword via the Kinopoisk API.

    Parameters:
    -----------
        query (str):
            The keyword to search for movies.
        token (str):
            User's authentication token.

    Returns:
    --------
        A list of Movie objects corresponding to the found movies.

    Exceptions:
    ----------
        Raises an HTTPException with status code 404 if no movies are found for the given query.

    Notes:
    ------
         This function calls get_kinopoisk_data() to fetch data from the Kinopoisk API.
    """
    params = {"keyword": query}
    headers = {
        "X-API-KEY": settings.KINOPOISK_API_KEY,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    data = await get_kinopoisk_data(
        "https://api.kinopoiskapiunofficial.tech/api/v2.1/films/search-by-keyword",
        params,
        headers=headers
    )

    if not data or 'films' not in data:
        raise HTTPException(status_code=404, detail="No films found for the given query")

    return [
        Movie(
            kinopoisk_id=movie.get('filmId'),
            title=movie.get('nameRu', 'Unknown Title'),
            year=parse_year(movie.get('year')),
            description=movie.get('description', ''),
            rating=parse_rating(movie.get('rating'))
        ) for movie in data['films']
    ]


def parse_year(year: str) -> int | None:
    """
    Description:
    ------------
        Converts a string representing a movie's year to an integer or None.

    Parameters:
    -----------
        year (str):
            The year of the movie as a string.

    Returns:
    --------
        int(year) | None

        Returns an integer if the string can be successfully converted to a year, otherwise returns None.

    Notes:
    ------
         If the year cannot be converted to an integer, the function returns None.
    """
    if year == 'null' or year is None:
        return None
    try:
        return int(year)
    except ValueError:
        # Если не удалось преобразовать в int, возвращаем None
        return None


def parse_rating(rating: str) -> float | None:
    """
    Description:
    ------------
        Converts a string representing a movie's rating to a float or None.

    Parameters:
    -----------
        rating (str):
            The rating of the movie as a string.

    Returns:
    -------
        float(rating) | None

        Returns a float if the string can be successfully converted to a rating, otherwise returns None.

    Notes:
    ------
         If the rating cannot be converted to a float, the function returns None.
    """
    if rating == 'null' or rating is None:
        return None
    try:
        return float(rating)
    except ValueError:
        # Если не удалось преобразовать в float, возвращаем None
        return None


# Эндпойнт для получения деталей фильма
@router.get("/movies/{kinopoisk_id}", response_model=MovieDetail)
async def get_movie_details(kinopoisk_id: int, token: str = Depends(get_current_user)):
    """
    Description:
    ------------
        Endpoint to retrieve detailed information about a movie by its Kinopoisk ID.

    Parameters:
    -----------
        kinopoisk_id (int):
            The movie's unique identifier in the Kinopoisk system.
        token (str):
            User's authentication token.

    Returns:
    --------
        A MovieDetail object containing detailed movie data such as title, description, year, rating, and other attributes.

    Exceptions:
    ----------
        Raises an HTTPException with status code 404 if the movie is not found.

    Notes:
    ------
        This function calls get_kinopoisk_data() to fetch movie details from the Kinopoisk API.
    """

    headers = {
        "X-API-KEY": settings.KINOPOISK_API_KEY,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = await get_kinopoisk_data(
        f"https://api.kinopoiskapiunofficial.tech/api/v2.2/films/{kinopoisk_id}",
        headers=headers
    )

    if not data:
        raise HTTPException(status_code=404, detail="Film not found")

    movie_data = data

    genres = [genre['genre'] for genre in movie_data.get('genres', [])]
    countries = [country['country'] for country in movie_data.get('countries', [])]

    return MovieDetail(
        kinopoisk_id=movie_data['kinopoiskId'],
        title=movie_data['nameRu'],
        year=movie_data['year'],
        description=movie_data.get('description', ''),
        rating=movie_data.get('rating', None),
        countries=countries,
        genres=genres,
        director=movie_data.get('director', ''),
        actors=movie_data.get('actors', []),
        duration=movie_data.get('duration', None),
        poster_url=movie_data.get('posterUrl', '')
    )


# Эндпойнт для добавления фильма в избранное
@router.post("/movies/favorites", response_model=FavoriteOut)
async def add_to_favorites(movie: FavoriteCreate,
                           token: dict = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    """
    Description:
    -----------
        Endpoint to add a movie to the user's favorites list.

    Parameters:
    -----------
        movie (FavoriteCreate):
            An object containing the movie data to be added to the favorites list.
        token (str):
            User's authentication token.
        db (AsyncSession):
            An asynchronous database session to interact with the storage.

    Returns:
    --------
        A FavoriteOut object representing the added movie in the favorites list.

    Exceptions:
    -----------
        Raises an HTTPException with status code 400 if the movie is already in the user's favorites.
    """
    user = token
    movie_in_db = await get_favorites_by_user(
        db,
        user_id=user['id'],
        kinopoisk_id=movie.kinopoisk_id
    )

    if movie_in_db:
        raise HTTPException(status_code=400, detail="Movie already in favorites")

    added_movie_to_favorite = await create_favorite(
        db,
        user_id=user['id'],
        kinopoisk_id=movie.kinopoisk_id,
        title=movie.title,
        year=movie.year
    )
    return added_movie_to_favorite


# Эндпойнт для удаления фильма из избранного
@router.delete("/movies/favorites/{kinopoisk_id}", response_model=FavoriteOut)
async def remove_from_favorites(kinopoisk_id: int,
                                token: dict = Depends(get_current_user),
                                db: AsyncSession = Depends(get_db)):
    """
    Description:
    ------------
        Endpoint to remove a movie from the user's favorites list.

    Parameters:
    -----------
        kinopoisk_id (int):
            The Kinopoisk ID of the movie to be removed from favorites.
        token (str):
            User's authentication token.
        db (AsyncSession):
            An asynchronous database session to interact with the storage.

    Returns:
    --------
        A FavoriteOut object representing the removed movie from the favorites list.

    Exceptions:
    -----------
        Raises an HTTPException with status code 404 if the movie is not found in the user's favorites.
    """
    user = token
    movie_in_db = await get_favorites_by_user(db, user_id=user['id'], kinopoisk_id=kinopoisk_id)

    if not movie_in_db:
        raise HTTPException(status_code=404, detail="Movie not found in favorites")

    removed_movie = await remove_favorite(db, user_id=user['id'], kinopoisk_id=kinopoisk_id)
    return removed_movie


# Эндпойнт для просмотра списка избранных фильмов
@router.get("/favorites", response_model=list[FavoriteOut])
async def get_favorites(token: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Description:
    -----------
        Endpoint to retrieve the list of all favorite movies for a user.

    Parameters:
    -----------
        token (str):
            User's authentication token.
        db (AsyncSession):
            An asynchronous database session to interact with the storage.

    Returns:
    --------
        A list of FavoriteOut objects representing the user's favorite movies.
    """
    user = token
    favorites = await get_favorite_with_user_id(db, user_id=user['id'])
    return favorites
