from src.core.log import get_logger
from src.exceptions.database import ExistingUserException
from src.interface.user_repo import AbstractUserRepo
from src.interface.user_service import AbstractUserService
from src.models.user import User
from src.schema.user import UserCreate, UserLogin

logger = get_logger(__name__)


class UserService(AbstractUserService):
    def __init__(self, repo: AbstractUserRepo):
        self.repo = repo

    def login_user(self, user: UserLogin) -> None:
        logger.info(f"user login: {user}")
        user = self.repo.authenticate_user(user=user)
        return user

    def register_user(self, user: UserCreate) -> User:
        existing_user = self.repo.fetch_existing_user_by_email(email=user.email)
        if existing_user:
            raise ExistingUserException(
                message=f"User with {user.email} already exists"
            )

        created_user = self.repo.create_user(user=user)
        return created_user
