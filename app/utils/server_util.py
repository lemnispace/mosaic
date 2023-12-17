from PIL import Image
import io
from fastapi import HTTPException


async def load_image_file(file):
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


def image_to_bytes(image):
    """
    Converts a PIL image to a byte array.

    Args:
        image: The PIL image to be converted.

    Returns:
        The byte array representation of the image.
    """
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="PNG")
    return img_byte_arr
