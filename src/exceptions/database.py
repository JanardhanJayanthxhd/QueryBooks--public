from src.exceptions.base import BaseAppException


class ExistingUserException(BaseAppException):
    def __init__(self, message: str) -> None:
        super().__init__(
            message=message, status_code=409, error_code="USER_ALREADY_EXISTS"
        )
