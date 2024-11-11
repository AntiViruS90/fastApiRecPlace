from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User, Favorite
from sqlalchemy.exc import IntegrityError
from app.core.security import hash_password


async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalars().first()


async def create_user(db: AsyncSession, username: str, password: str):
    """
        Create a new user in the database.

        This function attempts to create a new user with the given username and password.
        The password is hashed before storing in the database for security.

        Parameters:
        -----------
            db : AsyncSession
                The database session used for the operation.
            username : str
                The username for the new user. Must be unique.
            password : str
                The password for the new user. Will be hashed before storage.

        Returns:
        --------
            User | None
                Returns the created User object if successful, or None if a user with the given username already exists.

        Notes:
        ------
            If a duplicate username is encountered, the function will return None after rolling back the transaction.
        """
    hashed_password = hash_password(password)
    user = User(username=username, hashed_password=hashed_password)
    db.add(user)
    try:
        await db.commit()
        return user
    except IntegrityError:
        await db.rollback()
        return None


async def create_favorite(db: AsyncSession, user_id: int, kinopoisk_id: int, title: str, year: int):
    """
        Create a new favorite movie entry for a user in the database.

        This function creates a new Favorite object with the provided information,
        adds it to the database, commits the transaction, and refreshes the object.

        Parameters:
        -----------
            db : AsyncSession
                The database session used for the operation.
            user_id : int
                The ID of the user adding the favorite movie.
            kinopoisk_id : int
                The Kinopoisk ID of the movie being added to favorites.
            title : str
                The title of the movie.
            year : int
                The release year of the movie.

        Returns:
        --------
            Favorite
                The newly created Favorite object that has been added to the database.
        """
    favorite = Favorite(user_id=user_id, kinopoisk_id=kinopoisk_id, title=title, year=year)
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)
    return favorite


# Получение списка фильмов по user_id
async def get_favorite_with_user_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(Favorite).filter(Favorite.user_id == user_id))

    return result.scalars().all()


# Получение избранного фильма по user_id и kinopoisk_id
async def get_favorites_by_user(db: AsyncSession, user_id: int, kinopoisk_id: int):
    """
    Retrieve a specific favorite movie for a user from the database.

    This function queries the database for a favorite movie entry that matches
    both the user_id and kinopoisk_id.

    Parameters:
    -----------
        db : AsyncSession
            The database session used for the operation.
        user_id : int
            The ID of the user whose favorite movie is being queried.
        kinopoisk_id : int
            The Kinopoisk ID of the movie to be retrieved from favorites.

    Returns:
    --------
        Favorite | None
            Returns the Favorite object if found, or None if no matching favorite is found.
    """
    stmt = select(Favorite).filter(Favorite.user_id == user_id, Favorite.kinopoisk_id == kinopoisk_id)

    result = await db.execute(stmt)
    return result.scalars().first()


# Удаление фильма из избранных
async def remove_favorite(db: AsyncSession, user_id: int, kinopoisk_id: int):
    """
    Remove a favorite movie entry from the database for a specific user.

    This function retrieves a favorite movie entry from the database that matches the provided user_id and kinopoisk_id.
    If a matching favorite is found, it is deleted from the database and the transaction is committed.

    Parameters:
    -----------
    db : AsyncSession
        The database session used for the operation.
    user_id : int
        The ID of the user whose favorite movie is being removed.
    kinopoisk_id : int
        The Kinopoisk ID of the movie to be removed from favorites.

    Returns:
    --------
    Favorite | None
        Returns the deleted Favorite object if found and removed successfully, or None if no matching favorite is found.
    """
    favorite = await get_favorites_by_user(db, user_id, kinopoisk_id)
    if favorite:
        await db.delete(favorite)
        await db.commit()
    return favorite
