from pydantic import BaseModel, Field, HttpUrl


class Query(BaseModel):
    """
    pydantic model for user query
    """

    query: str = Field(min_length=1)


class WebLink(BaseModel):
    """
    pydantic model for web url
    """

    url: HttpUrl
