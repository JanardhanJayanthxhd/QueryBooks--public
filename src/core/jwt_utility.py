from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.core.jwt import decode_access_token
from src.core.log import get_logger
from src.models.user import User

security = HTTPBearer()
logger = get_logger(__name__)


def authenticate_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Authenticates a user by validating a JWT access token and verifying the user in the database.

    This function serves as a FastAPI dependency. It extracts the bearer token from the
    request headers, decodes it to retrieve user information, and ensures the
    corresponding user exists in the PostgreSQL database.

    Args:
        credentials (HTTPAuthorizationCredentials): The authorization credentials
            containing the JWT token, automatically extracted by FastAPI security.
        db (Session): The SQLAlchemy database session provided via dependency injection.

    Returns:
        User: The SQLAlchemy User object representing the authenticated user.

    Raises:
        HTTPException:
            - 401 Unauthorized: If the token is invalid, expired, or the user
              associated with the token ID no longer exists in the database.
    """
    token = credentials.credentials
    token_data = decode_access_token(token=token)
    logger.info(f"User info from token: {token_data}")
    user = db.query(User).filter_by(id=token_data.id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return user
