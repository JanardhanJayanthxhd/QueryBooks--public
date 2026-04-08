import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.api.routes import ai, chat, data, user
from src.core.config import lifespan
from src.core.log import get_logger, setup_logging
from src.exceptions.base import BaseAppException

setup_logging()
logger = get_logger(__name__)
app = FastAPI(lifespan=lifespan)
app.include_router(ai.ai)
app.include_router(chat.chat)
app.include_router(data.data)
app.include_router(user.user)


@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exec: BaseAppException):
    return JSONResponse(
        status_code=exec.status_code,
        content={"error": exec.error_code, "message": exec.message},
    )


@app.get("/")
async def hw():
    logger.info("Hi from /!")
    return {"jello": "world"}


# TO RUN LOCALLY
if __name__ == "__main__":
    uvicorn.run(app, port=5002, host='0.0.0.0')
