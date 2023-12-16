from fastapi.middleware.cors import CORSMiddleware
from utils.server_util import image_to_bytes, load_image_file
from services.gen_text_mosaic import gen_text_mosaic
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import FastAPI, Request, UploadFile, File, Form
from typing import Optional
from utils.config import get_env_variable, configure_logging

app = FastAPI(
    title="Text Mosaic API",
    description="API to generate a text mosaic image",
    version="0.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_env_variable("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = configure_logging()


@app.exception_handler(Exception)
async def universal_exception_handler(request: Request, exc: Exception):
    """
    Exception handler for handling unhandled exceptions in the API.

    Args:
        request (Request): The incoming request.
        exc (Exception): The unhandled exception.

    Returns:
        JSONResponse: The JSON response with an error message and status code 500.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"message": "Internal Server Error"})


@app.post("/mosaic")
async def mosaic(
    text: str = Form(..., description="Text to use for the mosaic"),
    width: Optional[int] = Form(
        3840, description="Desired width of the generated mosaic image"
    ),
    file: UploadFile = File(..., description="Image to use for the mosaic"),
):
    img = await load_image_file(file)
    if img is None:
        return JSONResponse(status_code=400, content={"message": "Invalid image"})
    text_mosaic = gen_text_mosaic(text, img, width)
    img_bytes = image_to_bytes(text_mosaic)
    img_bytes.seek(0)
    # Return the image directly as a response
    return StreamingResponse(img_bytes, media_type="image/png")
