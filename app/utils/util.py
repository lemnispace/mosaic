from PIL import ImageFont, ImageDraw
from PIL.Image import Image
from pathlib import Path
from typing import Tuple, Optional
import re
import io


def get_absolute_path(relative_path: str, base_path: Optional[Path] = None) -> Path:
    """
    Returns the absolute path of a file given its relative path.

    Args:
        relative_path: Path relative to base_path.
        base_path: Base directory for resolving relative path. Defaults to this file's directory.

    Returns:
        Resolved absolute path.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if base_path is None:
        base_path = Path(__file__).parent
    abs_path = base_path / relative_path
    abs_path = abs_path.resolve()
    if not abs_path.is_file():
        raise FileNotFoundError(f"File not found: {abs_path}")
    return abs_path


def clean_text(text: str) -> str:
    """
    Cleans the given text by removing extra whitespace, newlines, and tabs.

    Args:
        text: The text to be cleaned.

    Returns:
        The cleaned text with normalized whitespace.
    """
    return re.sub(r"\s+", " ", text).strip()


def get_charsize(
    font: ImageFont.FreeTypeFont,
    draw: ImageDraw.ImageDraw,
    char: str = "A",
) -> Tuple[int, int]:
    """
    Calculate the width and height of a character in pixels.

    Args:
        font: The font used to draw the character.
        draw: The drawing context.
        char: The character to measure (default: 'A').

    Returns:
        Tuple of (width, height) in pixels.
    """
    char_size = draw.textbbox((0, 0), char, font=font)
    char_width = char_size[2] - char_size[0]
    char_height = char_size[3] - char_size[1]
    return char_width, char_height


def image_to_bytes(image: Image, format: str = "PNG") -> io.BytesIO:
    """
    Converts a PIL image to a byte stream.

    Args:
        image: The PIL image to be converted.
        format: The image format (e.g., 'PNG', 'JPEG').

    Returns:
        BytesIO object containing the image data.
    """
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format=format)
    return img_byte_arr
