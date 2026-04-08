from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from src.core.constants import ResponseType
from src.core.jwt_utility import authenticate_user_from_token
from src.core.log import get_logger
from src.interface.data_service import AbstractDataService
from src.interface.user_service import AbstractUserService
from src.models.user import User
from src.repository.data_repo import DataRepository
from src.schema.ai import WebLink
from src.schema.response import APIResponse
from src.services.data_service import DataService

data = APIRouter()
logger = get_logger(__name__)


def get_data_service() -> AbstractDataService:
    return DataService(repo=DataRepository())


@data.post("/data/upload_pdf", response_model=APIResponse)
async def upload_pdf_to_db(
    file: UploadFile = File(...),
    current_user: User = Depends(authenticate_user_from_token),
    data_service: AbstractUserService = Depends(get_data_service),
):
    """
    Uploads a PDF file and stores its content as embeddings in the vector database.

    Only accepts files with a '.pdf' extension. Reads the file content and
    calls the function to process and add the embeddings.

    Args:
        file: The uploaded file, expected to be a PDF.

    Returns:
        A dictionary with the response status and a message containing the
        database's response upon successful embedding addition.

    Raises:
        HTTPException: If an error occurs during file reading or embedding
                       generation, a 400 Bad Request is raised.
    """

    if not file.filename.endswith(".pdf"):
        message = "Only supports .pdf files"
        logger.error(message)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=message
        )

    try:
        contents = await file.read()
        file_add_response = data_service.add_pdf_as_embedding(
            content=contents, filename=file.filename, user_id=current_user.id
        )
        return APIResponse(
            response=ResponseType.SUCCESS,
            message={
                "db response": file_add_response,
            },
        )
    except Exception as e:
        logger.error(f"Error {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while uploading file. Please try again.",
        )


@data.post("/data/upload_web_content", response_model=APIResponse)
async def upload_blog_to_db(
    blog_url: WebLink,
    current_user: User = Depends(authenticate_user_from_token),
    data_service: AbstractDataService = Depends(get_data_service),
):
    """
    Fetches content from a specified URL (e.g., a blog) and stores it as
    embeddings in the vector database.

    The URL is extracted from the BlogLink schema and the web content is
    processed for embedding generation.

    Args:
        blog_url: A BlogLink schema object containing the URL of the web content.

    Returns:
        A dictionary with the response status and a message containing the
        database's response upon successful embedding addition.

    Raises:
        HTTPException: If an error occurs during web content retrieval or
                       embedding generation, a 400 Bad Request is raised.
    """
    try:
        web_upload_result = data_service.add_web_content_as_embedding(
            url=str(blog_url.url), user_id=current_user.id
        )
        return APIResponse(
            response=ResponseType.SUCCESS,
            message={
                "db response": web_upload_result,
            },
        )
    except Exception as e:
        logger.error(f"Error {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while uploading web content. Please try again.",
        )
