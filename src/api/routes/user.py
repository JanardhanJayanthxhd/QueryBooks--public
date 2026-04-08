from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.constants import ResponseType
from src.core.database import get_db
from src.core.jwt import create_access_token
from src.core.log import get_logger
from src.interface.user_service import AbstractUserService
from src.repository.user_repo import UserRepository
from src.schema.response import APIResponse
from src.schema.user import UserCreate, UserLogin, UserResponse
from src.services.user_service import UserService

user = APIRouter()
logger = get_logger(__name__)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(repo=UserRepository(session=db))


@user.post("/user/register", response_model=APIResponse)
def register_user(
    user_create: UserCreate,
    user_service: AbstractUserService = Depends(get_user_service),
):
    try:
        created_user = user_service.register_user(user=user_create)
        return APIResponse(
            response=ResponseType.SUCCESS,
            message={
                "result": "Successfully added user to database",
                "user details": UserResponse(
                    name=created_user.name, email=created_user.email
                ),
            },
        )
    except Exception as e:
        message = f"Error occured: {e}"
        logger.error(message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occured try again later",
        )


@user.post("/user/login", response_model=APIResponse)
def login_user(
    user_login: UserLogin,
    user_service: AbstractUserService = Depends(get_user_service),
):
    try:
        user = user_service.login_user(user=user_login)
        token = create_access_token(
            data={"email": user.email, "id": user.id}, expires_delta=None
        )
        logger.debug(f"JWT TOKEN: {token}")
        return APIResponse(response=ResponseType.SUCCESS, message={"token": token})
    except HTTPException:
        raise
    except Exception as e:
        message = f"Error occured: {e}"
        logger.error(message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occured try again later",
        )
