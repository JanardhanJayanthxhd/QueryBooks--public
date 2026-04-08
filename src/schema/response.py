from typing import Any

from pydantic import BaseModel, Field
from src.core.constants import ResponseType


class APIResponse(BaseModel):
    """A standardized structure for all API responses.

    This model ensures that every API call returns a consistent format,
    making it easier for frontend clients to parse success and error states.

    Attributes:
        response (ResponseType): The status of the request, typically 'success' or 'fail'.
        message (dict[str, Any]): A dictionary containing the actual payload or
            detailed error information.

    Config:
        use_enum_values (bool): Set to True to ensure that Enum members in
            'response' are serialized to their underlying values (e.g., strings).
    """

    response: ResponseType = Field(..., description="type of response success or fail")
    message: dict[str, Any] = Field(..., description="message dictionary")

    class Config:
        use_enum_values = True
