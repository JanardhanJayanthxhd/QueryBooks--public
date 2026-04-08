from pydantic import BaseModel, EmailStr


class TokenData(BaseModel):
    """Data structure for the payload extracted from a decoded JWT.

    This model is used during the authentication dependency phase to
    verify the identity of the user requesting a protected resource.

    Attributes:
        email (EmailStr): The verified email address of the user.
        id (int): The unique database identifier for the user.
    """

    email: EmailStr
    id: int
