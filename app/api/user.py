from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import oauth2_scheme
from app.db import crud
from app.db.session import get_db
from schemas import UserCreate, UserOut, Token
from app.core.security import verify_password
from app.core.core_jwt import create_access_token, decode_access_token

router = APIRouter()


@router.post("/register", response_model=UserOut)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Description:
    -----------
        Registers a new user in the system.

    Parameters:
    -----------
        user (UserCreate):
            A Pydantic model containing the username and password of the new user.
        db (AsyncSession, optional):
            An asynchronous database session, automatically provided by Depends(get_db). Defaults to None.

    Returns:
    --------
        UserOut:
            A Pydantic model representing the newly created user.

    Raises:
    -------
        HTTPException:
            If the username is already registered, it raises a 400 status code with the message "Username already registered".
        HTTPException:
            If there is an error creating the user, it raises a 500 status code with the message "Error creating user".
        """
    existing_user = await crud.get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    created_user = await crud.create_user(db, user.username, user.password)
    if not created_user:
        raise HTTPException(status_code=500, detail="Error creating user")
    return created_user


@router.post("/login", response_model=Token)
async def login_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Description:
    -----------
        Endpoint for user login. It validates the username and password against the database and returns an access token
            if the credentials are valid.

    Parameters:
    -----------
        user (UserCreate):
            A Pydantic model containing the username and password of the user attempting to log in.
        db (AsyncSession, optional):
            An asynchronous database session, automatically provided by Depends(get_db).

    Returns:
    --------
        A dictionary containing the access token and the token type (bearer).

    Exceptions:
    ----------
        Raises an HTTPException with status code 401 if the credentials (username or password) are invalid.

    Notes:
    ------
        The function checks if the username exists in the database and if the provided password
            matches the stored hashed password.
        If valid, it generates a JWT access token using create_access_token() and returns it along with the
            token type (bearer).
    """
    db_user = await crud.get_user_by_username(db, user.username)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": db_user.username, "id": db_user.id})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/profile", response_model=UserOut)
async def get_user_profile(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """
    Description:
    ------------
        Endpoint for fetching the authenticated user's profile.
        It decodes the access token and retrieves the user's details from the database.

    Parameters:
    -----------
        token (str):
            The user's access token provided in the request's Authorization header. It is extracted using the Depends(oauth2_scheme) dependency.
        db (AsyncSession, optional):
            An asynchronous database session, automatically provided by Depends(get_db).

    Returns:
    --------
        A UserOut object containing the user's profile details.

    Exceptions:
    ----------
        Raises an HTTPException with status code 401 if the token is invalid or expired.
        Raises an HTTPException with status code 404 if the user corresponding to the token is not found.

    Notes:
    ------
        The function decodes the JWT access token using decode_access_token() to extract the username.
        It checks if the username exists in the database and returns the user's profile if found.
        If the token is invalid or expired, the user is unauthorized and an error is raised.
    """

    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

    db_user = await crud.get_user_by_username(db, username)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    print(token)
    return db_user
