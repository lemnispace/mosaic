from PIL import Image
import io
from typing import Optional
from fastapi import HTTPException, UploadFile, FastAPI
from utils.config import get_env_variable
from mangum import Mangum
import logging

logger = logging.getLogger(__name__)

# Security limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGE_DIMENSION = 10000  # pixels


async def load_image_file(file: UploadFile) -> Optional[Image.Image]:
    """
    Loads and validates an image file with security checks.

    Args:
        file: The file object representing the image file.

    Returns:
        The loaded and validated PIL image, or None if invalid.

    Raises:
        HTTPException: If the image file is invalid, too large, or malicious.
    """
    # Validate content type
    if not file.content_type or not file.content_type.startswith("image/"):
        logger.warning(f"Invalid content type: {file.content_type}")
        raise HTTPException(status_code=400, detail="Invalid content type. Must be an image.")

    # Read file with size limit to prevent memory exhaustion
    image_data = await file.read(MAX_FILE_SIZE + 1)

    if len(image_data) > MAX_FILE_SIZE:
        logger.warning(f"File too large: {len(image_data)} bytes")
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    if len(image_data) == 0:
        logger.warning("Empty file uploaded")
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        # Initial image opening
        image = Image.open(io.BytesIO(image_data))

        # Verify image integrity (detects corrupted images)
        image.verify()

        # Reopen after verify (verify closes the file)
        image = Image.open(io.BytesIO(image_data))

        # Validate image dimensions
        if image.width > MAX_IMAGE_DIMENSION or image.height > MAX_IMAGE_DIMENSION:
            logger.warning(f"Image dimensions too large: {image.width}x{image.height}")
            raise HTTPException(
                status_code=400,
                detail=f"Image dimensions too large. Maximum is {MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION} pixels"
            )

        if image.width < 1 or image.height < 1:
            logger.warning(f"Invalid image dimensions: {image.width}x{image.height}")
            raise HTTPException(status_code=400, detail="Invalid image dimensions")

        # Load image data to detect decompression bombs
        try:
            image.load()
        except Image.DecompressionBombError as e:
            logger.error(f"Decompression bomb detected: {e}")
            raise HTTPException(status_code=400, detail="Image file is too large when decompressed")

        logger.info(f"Image loaded successfully: {image.width}x{image.height}, mode={image.mode}")
        return image

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except (IOError, OSError, Image.DecompressionBombError) as e:
        logger.error(f"Invalid image upload: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid or malicious image file")


def get_asgi_handler(stage: Optional[str], app: FastAPI) -> Mangum:
    """
    Get the ASGI handler for the API.

    Args:
        stage: The deployment stage of the API (e.g., 'Dev', 'Prod').

    Returns:
        Mangum ASGI handler configured with the appropriate root path.
    """
    root_path = get_env_variable("ROOT_PATH", "")
    app.root_path = f"/{stage}/{root_path}" if stage else f"/{root_path}"
    return Mangum(app, api_gateway_base_path=app.root_path)


def get_stage(event: dict) -> Optional[str]:
    """
    Get the deployment stage of the API from the Lambda event data.

    Args:
        event: The Lambda event dictionary.

    Returns:
        The stage name or None if not found.
    """
    stage_variables = event.get("stageVariables", {})
    return stage_variables.get("Stage", None) if stage_variables else None
