from pathlib import Path
import re
from PIL import ImageFont, ImageDraw


def get_absolute_path(relative_path: str):
    """Returns the absolute path of a file given its relative path."""
    abs_path = Path(__file__).parent / relative_path
    abs_path = abs_path.resolve()
    if not abs_path.is_file():
        raise FileNotFoundError(f"File not found: {abs_path}")
    return abs_path


def clean_text(text: str) -> str:
    """
    Cleans the given text by removing extra whitespace, newlines, and tabs

    Args:
        text (str): The text to be cleaned.

    Returns:
        str: The cleaned text.
    """
    return re.sub(r"\s+", " ", text).strip()


def get_charsize(
    font: ImageFont.FreeTypeFont,
    draw: ImageDraw.ImageDraw,
    char: str = "A",
):
    """
    Calculate the width and height of a character.

    Args:
        char (str): The character to measure.
        font (ImageFont.FreeTypeFont): The font used to draw the character.
        draw (ImageDraw.ImageDraw): The drawing context.

    Returns:
        Tuple[int, int]: The width and height of the character.
    """
    char_size = draw.textbbox((0, 0), char, font=font)
    char_width = char_size[2] - char_size[0]
    char_height = char_size[3] - char_size[1]
    return char_width, char_height
