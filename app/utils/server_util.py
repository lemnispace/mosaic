from PIL import Image
import io
from fastapi import HTTPException, UploadFile, FastAPI
from utils.config import get_env_variable
from mangum import Mangum


async def load_image_file(file: UploadFile):
    """
    Loads an image file from the given file object.

    Args:
        file: The file object representing the image file.

    Returns:
        The loaded PIL image.

    Raises:
        HTTPException: If the image file is invalid.
    """
    if file.content_type.startswith("image/"):
        # Read image file and convert it to a PIL image
        image_data = await file.read()
        try:
            image = Image.open(io.BytesIO(image_data))
            return image
        except (IOError, OSError) as e:
            raise HTTPException(status_code=400, detail="Invalid image")


def get_asgi_handler(stage: str | None, app: FastAPI):
    """
    Get the ASGI handler for the API.

    Args:
        stage (str | None): The stage of the API.

    Returns:
        Mangum: The Mangum ASGI handler.
    """
    root_path = get_env_variable("ROOT_PATH", "ai-gen")
    app.root_path = f"/{stage}/{root_path}" if stage else f"/{root_path}"
    return Mangum(app, api_gateway_base_path=app.root_path)


def get_stage(event):
    """
    Get the deployment stage of the API from the event data.

    Args:
        event: The event data.

    Returns:
        str | None: The stage of the API.
    """
    stage_variables = event.get("stageVariables", {})
    return stage_variables.get("Stage", None) if stage_variables else None
