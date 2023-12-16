from PIL import Image
import io
from fastapi import HTTPException


async def load_image_file(file):
    if file.content_type.startswith("image/"):
        # Read image file and convert it to a PIL image
        image_data = await file.read()
        try:
            image = Image.open(io.BytesIO(image_data))
            return image
        except (IOError, OSError) as e:
            raise HTTPException(status_code=400, detail="Invalid image")


def image_to_bytes(image):
    """Converts a PIL image to a byte array"""
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="PNG")
    return img_byte_arr
