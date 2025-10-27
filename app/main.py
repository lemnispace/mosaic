from fastapi.middleware.cors import CORSMiddleware
from utils.server_util import (
    load_image_file,
    get_asgi_handler,
    get_stage,
)
from utils.config import Config, configure_logging
from utils.util import image_to_bytes, get_absolute_path
from services.gen_text_mosaic import gen_text_mosaic
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import FastAPI, Request, UploadFile, File, Form
from typing import Optional
from contextvars import ContextVar
import json
import time
import uuid

# Load and validate configuration
config = Config.from_env()
config.validate()

# Configure logging
logger = configure_logging(config.log_level)

# Context variable for request tracking
request_id_var: ContextVar[str] = ContextVar('request_id', default='')

app = FastAPI(
    title="Text Mosaic API",
    description="""
## Text Mosaic Generation Service

Transforms images into artistic text mosaics by overlaying customizable text
that matches the colors and contrast of the original image.

### Features
- Automatic font scaling based on image resolution
- Black & white conversion option
- Contrast adjustment
- Supports PNG, JPEG, WebP, and other common formats

### Limits
- Max image size: 10MB
- Max dimensions: 10,000 x 10,000 pixels
- Processing timeout: 60 seconds
    """,
    version="1.0.0",
    contact={
        "name": "LemniSpace",
    },
)

# Add CORS middleware with validated configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.allowed_origins,
    allow_credentials=config.allow_credentials,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """
    Middleware to add request ID tracking and performance monitoring.

    Args:
        request: The incoming HTTP request.
        call_next: The next middleware or route handler.

    Returns:
        Response with added X-Request-ID header.
    """
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)

    start_time = time.time()

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log request completion
        logger.info(json.dumps({
            "request_id": request_id,
            "event": "request_completed",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(process_time * 1000, 2),
        }))

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(json.dumps({
            "request_id": request_id,
            "event": "request_failed",
            "method": request.method,
            "path": request.url.path,
            "error": str(e),
            "duration_ms": round(process_time * 1000, 2),
        }), exc_info=True)
        raise


@app.exception_handler(Exception)
async def universal_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions.

    Args:
        request: The incoming request.
        exc: The unhandled exception.

    Returns:
        JSONResponse with error details and 500 status code.
    """
    request_id = request_id_var.get('')
    logger.error(json.dumps({
        "request_id": request_id,
        "event": "unhandled_exception",
        "error": str(exc),
        "path": request.url.path,
    }), exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal Server Error",
            "request_id": request_id,
        }
    )


@app.get("/health", tags=["monitoring"])
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.

    Returns:
        JSON with service status.
    """
    return {
        "status": "healthy",
        "service": "text-mosaic-api",
        "version": app.version,
    }


@app.get("/readiness", tags=["monitoring"])
async def readiness_check():
    """
    Readiness check - verifies service can handle requests.
    Checks that required resources (fonts) are accessible.

    Returns:
        JSON with readiness status or 503 if not ready.
    """
    try:
        # Verify font file exists
        font_path = get_absolute_path("../fonts/NotoSansMono-Black.ttf")

        return {
            "status": "ready",
            "service": "text-mosaic-api",
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "reason": str(e),
            }
        )


@app.post(
    "/",
    summary="Generate text mosaic",
    description="Upload an image and text to create a text-based mosaic visualization",
    response_description="PNG image with text mosaic overlay",
    responses={
        200: {
            "description": "Successfully generated mosaic",
            "content": {"image/png": {}},
        },
        400: {"description": "Invalid image or parameters"},
        413: {"description": "Image file too large"},
        422: {"description": "Invalid request parameters"},
        500: {"description": "Server error during processing"},
    },
)
async def mosaic(
    text: str = Form(..., description="Text to use for the mosaic", min_length=1),
    width: Optional[int] = Form(
        3840,
        description="Desired width of the generated mosaic image",
        ge=100,
        le=10000,
    ),
    base_font_size: Optional[int] = Form(
        14,
        description="Base font size to use for the mosaic. The actual font size will be scaled based on the image size.",
        ge=6,
        le=100,
    ),
    is_black_and_white: Optional[bool] = Form(
        True, description="Whether to generate a black and white mosaic"
    ),
    contrast_factor: Optional[float] = Form(
        1.5,
        description="Factor to adjust the contrast of the image. A value of 1.0 means no change in contrast.",
        ge=0.0,
        le=5.0,
    ),
    file: UploadFile = File(..., description="Image to use for the mosaic"),
):
    """
    Generate a text mosaic from an uploaded image.

    The mosaic overlays the provided text onto the image, with each character
    colored to match the underlying pixel color.
    """
    request_id = request_id_var.get('')

    logger.info(json.dumps({
        "request_id": request_id,
        "event": "mosaic_request_received",
        "text_length": len(text),
        "target_width": width,
        "base_font_size": base_font_size,
        "is_bw": is_black_and_white,
        "contrast_factor": contrast_factor,
        "filename": file.filename,
        "content_type": file.content_type,
    }))

    # Validate text is not empty after stripping
    if not text.strip():
        logger.warning(json.dumps({
            "request_id": request_id,
            "event": "invalid_text",
            "reason": "Text is empty or whitespace only",
        }))
        return JSONResponse(
            status_code=400,
            content={"message": "Text cannot be empty"}
        )

    # Load and validate image
    img = await load_image_file(file)

    logger.info(json.dumps({
        "request_id": request_id,
        "event": "image_loaded",
        "original_size": f"{img.width}x{img.height}",
        "mode": img.mode,
    }))

    try:
        # Generate mosaic
        start_time = time.time()
        text_mosaic = gen_text_mosaic(
            text,
            img,
            target_width=width,
            text_size=base_font_size,
            is_black_and_white=is_black_and_white,
            contrast_factor=contrast_factor,
        )
        generation_time = time.time() - start_time

        logger.info(json.dumps({
            "request_id": request_id,
            "event": "mosaic_generated",
            "output_size": f"{text_mosaic.width}x{text_mosaic.height}",
            "generation_time_ms": round(generation_time * 1000, 2),
        }))

        # Convert to bytes
        img_bytes = image_to_bytes(text_mosaic, format="PNG")
        img_bytes.seek(0)

        logger.info(json.dumps({
            "request_id": request_id,
            "event": "mosaic_completed",
            "output_size_bytes": len(img_bytes.getvalue()),
        }))

        # Return the image
        return StreamingResponse(
            img_bytes,
            media_type="image/png",
            headers={"X-Request-ID": request_id},
        )

    except ValueError as e:
        logger.warning(json.dumps({
            "request_id": request_id,
            "event": "validation_error",
            "error": str(e),
        }))
        return JSONResponse(
            status_code=400,
            content={
                "message": str(e),
                "request_id": request_id,
            }
        )
    except Exception as e:
        logger.error(json.dumps({
            "request_id": request_id,
            "event": "mosaic_generation_failed",
            "error": str(e),
        }), exc_info=True)
        raise


def handler(event, context):
    """
    AWS Lambda handler function for the API.

    Args:
        event: The Lambda event data.
        context: The Lambda context data.

    Returns:
        dict: The response from the ASGI handler.
    """
    stage = get_stage(event)
    asgi_handler = get_asgi_handler(stage, app)

    try:
        response = asgi_handler(event, context)

        # Log Lambda invocation (but not full response body to save space)
        log_data = {
            "event": "lambda_invocation",
            "stage": stage,
            "statusCode": response.get("statusCode"),
            "root_path": app.root_path,
            "path": event.get("rawPath", ""),
            "method": event.get("requestContext", {}).get("http", {}).get("method", ""),
        }

        if response.get("statusCode", 500) >= 400:
            logger.error(json.dumps(log_data))
        else:
            logger.info(json.dumps(log_data))

        return response

    except Exception as e:
        logger.exception(json.dumps({
            "event": "lambda_handler_error",
            "error": str(e),
            "stage": stage,
        }), exc_info=True)

        # Return proper error response instead of re-raising
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": json.dumps({
                "message": "Internal server error",
            }),
        }
