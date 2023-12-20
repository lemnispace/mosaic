import pytest
from PIL import Image
from fastapi import UploadFile, HTTPException, FastAPI
from mangum import Mangum
import io
import os
from app.utils.config import get_env_variable
from app.utils.server_util import load_image_file, get_asgi_handler, get_stage


@pytest.fixture
def valid_image_file():
    # Create a small valid image using PIL
    image = Image.new("RGB", (10, 10), color="red")
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="PNG")
    img_byte_arr = img_byte_arr.getvalue()

    # Create a mock file-like object with valid image data
    return io.BytesIO(img_byte_arr)


@pytest.fixture
def valid_upload_img_file(valid_image_file):
    # Create an UploadFile with the mock object
    return UploadFile(
        file=valid_image_file,
        filename="filename.png",
        headers={"content-type": "image/png"},
    )


@pytest.mark.asyncio
async def test_load_image_file_valid_image(valid_upload_img_file):
    image = await load_image_file(valid_upload_img_file)
    assert isinstance(image, Image.Image)


@pytest.mark.asyncio
async def test_load_image_file_invalid_image():
    file_like_object = io.BytesIO(b"somefakeimagedata")
    # Create an UploadFile with the mock object
    file = UploadFile(
        file=file_like_object,
        filename="filename.png",
        headers={"content-type": "text/plain"},
    )
    try:
        await load_image_file(file)
    except HTTPException as e:
        assert e.status_code == 400
        assert e.detail == "Invalid image"


# Test get_asgi_handler function
def test_get_asgi_handler_with_stage():
    stage = "dev"
    app = FastAPI()
    handler = get_asgi_handler(stage, app)
    assert isinstance(handler, Mangum)
    assert app.root_path == f"/{stage}/"


def test_get_asgi_handler_without_stage():
    app = FastAPI()
    handler = get_asgi_handler(None, app)
    assert isinstance(handler, Mangum)
    assert app.root_path == "/"


def test_get_asgi_handler_with_env_variable():
    stage = "dev"
    app = FastAPI()
    os.environ["ROOT_PATH"] = "expected/root_path"
    handler = get_asgi_handler(stage, app)
    assert isinstance(handler, Mangum)
    assert app.root_path == f"/{stage}/expected/root_path"


# Test get_stage function
def test_get_stage_with_stage_variables():
    event = {"stageVariables": {"Stage": "testing"}}
    stage = get_stage(event)
    assert stage == "testing"


def test_get_stage_without_stage_variables():
    event = {}
    stage = get_stage(event)
    assert stage is None
