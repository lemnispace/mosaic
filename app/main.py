from fastapi.middleware.cors import CORSMiddleware
from utils.server_util import (
    load_image_file,
    get_asgi_handler,
    get_stage,
)
from utils.config import get_env_variable, configure_logging
from utils.util import image_to_bytes
from services.gen_text_mosaic import gen_text_mosaic
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import FastAPI, Request, UploadFile, File, Form
from typing import Optional
import json

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


@app.post("/")
async def mosaic(
    text: str = Form(..., description="Text to use for the mosaic"),
    width: Optional[int] = Form(
        3840, description="Desired width of the generated mosaic image"
    ),
    base_font_size: Optional[int] = Form(
        14,
        description="Base font size to use for the mosaic. The actual font size will be scaled based on the image size.",
    ),
    is_black_and_white: Optional[bool] = Form(
        True, description="Whether to generate a black and white mosaic"
    ),
    file: UploadFile = File(..., description="Image to use for the mosaic"),
):
    img = await load_image_file(file)
    if img is None:
        return JSONResponse(status_code=400, content={"message": "Invalid image"})
    text_mosaic = gen_text_mosaic(
        text,
        img,
        target_width=width,
        text_size=base_font_size,
        is_black_and_white=is_black_and_white,
    )
    img_bytes = image_to_bytes(text_mosaic, format="PNG")
    img_bytes.seek(0)
    # Return the image directly as a response
    return StreamingResponse(img_bytes, media_type="image/png")


def handler(event, context):
    """
    Lambda handler function for the API.

    Args:
        event: The event data.
        context: The context data.

    Returns:
        dict: The response from the ASGI handler.
    """
    stage = get_stage(event)
    asgi_handler = get_asgi_handler(stage, app)
    try:
        response = asgi_handler(event, context)
        log_data = {
            "stage": stage,
            "statusCode": response.get("statusCode", None),
            "root_path": app.root_path,
            "response": response,
            "event": event,
        }
        if response.get("statusCode") >= 400:
            logger.error(json.dumps(log_data))
        else:
            logger.info(json.dumps(log_data))
        return response
    except Exception as e:
        logger.exception("Error processing request.")
        raise
