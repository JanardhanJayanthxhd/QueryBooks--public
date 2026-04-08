from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Schema for creating a new user account.

    Includes all necessary fields for registration. This model automatically
    validates that the email provided follows a valid email format.

    Attributes:
        name (str): The full name or username of the user.
        email (EmailStr): A valid email address for account registration.
        password (str): The raw password string (to be hashed before storage).
    """

    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Schema for user authentication requests.

    Attributes:
        email (EmailStr): The email address associated with the account.
        password (str): The raw password to be verified against the stored hash.
    """

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for returning user data to the client.

    This model excludes sensitive information like 'password_hash' to
    ensure data privacy when sending user details over the network.

    Attributes:
        name (str): The user's name.
        email (EmailStr): The user's email address.
    """

    name: str
    email: EmailStr
