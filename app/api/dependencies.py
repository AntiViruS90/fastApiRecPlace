from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.core.core_jwt import decode_access_token
from app.db.session import get_db
from sqlalchemy.orm import Session

# OAuth2PasswordBearer используется для аутентификации
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# Зависимость для получения доступа к базе данных
def get_db_session(db: Session = Depends(get_db)):
    return db


# Зависимость для декодирования JWT токена
def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Description:
    ------------
        Authenticate and retrieve the current user based on the provided JWT token.

        This function decodes the access token, validates it, and returns the user information.
        If the token is invalid or expired, it raises an HTTPException.

    Args:
    ----
        token (str):
            The JWT token obtained from the OAuth2PasswordBearer dependency.

    Returns:
    --------
        dict:
            A dictionary containing the user information extracted from the token.

    Raises:
    ------
        HTTPException: If the authentication credentials are invalid (status code 401).
    """
    user = decode_access_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    return user
