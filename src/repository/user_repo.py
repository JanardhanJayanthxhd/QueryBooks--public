from typing import Optional

from sqlalchemy.orm import Session
from src.core.utility import hash_password, verify_password
from src.interface.user_repo import AbstractUserRepo
from src.models.user import User
from src.repository.utility import (
    add_commit_refresh_db,
    log_then_raise_unauthorized_error,
)
from src.schema.user import UserCreate, UserLogin


class UserRepository(AbstractUserRepo):
    def __init__(self, session: Session) -> None:
        self.session = session

    def fetch_existing_user_by_email(self, email: str) -> Optional[User]:
        return self.session.query(User).filter_by(email=email).first()

    def authenticate_user(self, user: UserLogin):
        db_user = self.fetch_existing_user_by_email(email=user.email)
        if not db_user:
            log_then_raise_unauthorized_error(
                message=f"Unable to find user with {user.email} id"
            )

        if not verify_password(
            plain_password=user.password, hashed_password=db_user.password_hash
        ):
            log_then_raise_unauthorized_error(message="Invalid email or password")

        return db_user

    def create_user(self, user: UserCreate) -> User:
        new_user = User(
            name=user.name,
            email=user.email,
            password_hash=hash_password(password=user.password),
        )

        add_commit_refresh_db(object=new_user, db=self.session)

        return new_user
