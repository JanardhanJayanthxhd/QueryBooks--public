from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.core.log import get_logger
from src.models.user import User

logger = get_logger(__name__)


def add_commit_refresh_db(object: User, db: Session):
    """Adds an object to the database, commits the transaction, and refreshes the instance.

    This helper function handles the standard SQLAlchemy lifecycle for a new or
    updated object to ensure the local instance matches the database state
    (including generated IDs or default values).

    Args:
        object (User): The SQLAlchemy model instance to be persisted.
        db (Session): The active database session.
    """
    db.add(object)
    db.commit()
    db.refresh(object)


def log_then_raise_unauthorized_error(message: str) -> None:
    """Logs an error message and raises an HTTP 401 Unauthorized exception.

    Args:
        message (str): The error message to be logged and sent back
            in the HTTP response detail.

    Raises:
        HTTPException: Always raises a 401 Unauthorized status code.
    """
    logger.error(message)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)
