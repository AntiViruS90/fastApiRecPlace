import jwt
from datetime import datetime, timedelta
from .config import settings


def create_access_token(data: dict, expires_delta: timedelta = None):
    """
        Creates a JWT access token using the provided data and expiration delta.

    Parameters:
    -----------
        data (dict):
            The data to be encoded into the JWT token. Must contain an 'id' field.
        expires_delta (timedelta, optional):
            The time delta for token expiration. If not provided, the token will expire
            after the time specified in the JWT_EXPIRATION_TIME setting.

    Returns:
    --------
        str:
            The generated JWT access token.
        """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(seconds=settings.JWT_EXPIRATION_TIME)

    to_encode.update({"exp": expire, "id": data["id"]})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str) -> dict:
    """
        Decodes a JWT access token and returns its payload.

    Parameters:
    -----------
        token (str):
            The JWT access token to decode.

    Returns:
    --------
        dict:
            The decoded payload from the JWT token.

    Exception:
    ---------
        If the token has expired, is invalid, or an unexpected error occurs.
        """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {str(e)}")
