from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from utils.util import get_absolute_path, clean_text, get_charsize
from functools import lru_cache
from typing import Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Memory limit for Lambda (leave buffer for overhead)
MAX_MEMORY_MB = 400


def gen_text_mosaic(
    text: str,
    img: Image.Image,
    target_width: int = 3840,
    text_size: int = 14,
    is_black_and_white: bool = True,
    contrast_factor: float = 1.5,
) -> Image.Image:
    """
    Generate a text mosaic image by repeating the given text to fill the image.
    The output image will be resized to the target width while maintaining the aspect ratio.

    Args:
        text: The text to be repeated in the text mosaic.
        img: The input image on which the text mosaic will be generated.
        target_width: The desired width of the output image.
        text_size: The base size of the text in the text mosaic.
        is_black_and_white: Whether to convert the image to black and white.
        contrast_factor: The factor to adjust the contrast of the image.

    Returns:
        The generated text mosaic image.

    Raises:
        ValueError: If inputs are invalid or memory requirements exceed limits.
    """
    # Validate inputs
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    if target_width < 100 or target_width > 10000:
        raise ValueError("target_width must be between 100 and 10000")

    if text_size < 6 or text_size > 100:
        raise ValueError("text_size must be between 6 and 100")

    if contrast_factor < 0 or contrast_factor > 5:
        raise ValueError("contrast_factor must be between 0 and 5")

    # Calculate target dimensions
    target_height = get_target_height(img, target_width)

    # Estimate memory requirements (3 RGBA images: original, processed, text overlay)
    estimated_memory_mb = (target_width * target_height * 4 * 3) / (1024 * 1024)

    if estimated_memory_mb > MAX_MEMORY_MB:
        raise ValueError(
            f"Image too large: estimated {estimated_memory_mb:.0f}MB memory required, "
            f"maximum is {MAX_MEMORY_MB}MB. Try reducing target_width or using a smaller image."
        )

    logger.info(
        f"Processing mosaic: {img.width}x{img.height} -> {target_width}x{target_height}, "
        f"estimated memory: {estimated_memory_mb:.1f}MB"
    )

    # Resize image
    resized = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    del img  # Explicit cleanup of original

    # Get font
    font = get_font(target_width, text_size)

    # Pre-process the image
    image, txt_img = pre_process_img(resized, is_black_and_white, contrast_factor)
    del resized  # Cleanup

    # Create a drawing context for the text image
    draw = ImageDraw.Draw(txt_img)

    # Pre-process the text
    processed_text = pre_process_text(text)

    # Generate the text mosaic
    gen_mosaic(image, processed_text, font, draw)

    # Cleanup before return
    del image, draw

    return txt_img


@lru_cache(maxsize=32)
def _load_font(font_size: int) -> ImageFont.FreeTypeFont:
    """
    Load and cache font objects by size for better performance.

    Args:
        font_size: The font size in points.

    Returns:
        The cached font object.
    """
    font_path = str(get_absolute_path("../fonts/NotoSansMono-Black.ttf"))
    return ImageFont.truetype(font_path, font_size)


def get_font(img_width: int, default_font_size: int = 14) -> ImageFont.FreeTypeFont:
    """
    Get the font object based on the target image width with resolution-based scaling.

    Args:
        img_width: The width of the target image in pixels.
        default_font_size: The base font size to scale from.

    Returns:
        The font object with appropriate size for the image width.
    """
    # Resolution-based scaling tiers (order matters - check smallest first)
    if img_width <= 480:
        multiplier = 0.5
    elif img_width <= 720:
        multiplier = 0.75
    elif img_width < 1080:
        multiplier = 1.0
    elif img_width < 2160:
        multiplier = 1.5
    elif img_width < 3300:
        multiplier = 2.0
    elif img_width < 3600:
        multiplier = 3.0
    elif img_width < 4800:
        multiplier = 3.5
    elif img_width < 7200:
        multiplier = 4.0
    else:
        multiplier = 4.5

    font_size = int(default_font_size * multiplier)
    logger.debug(f"Font scaling: width={img_width}px, multiplier={multiplier}x, size={font_size}pt")

    return _load_font(font_size)


def get_target_height(img: Image.Image, target_width: int) -> int:
    """
    Calculate the target height based on target width and aspect ratio.

    Args:
        img: The input image.
        target_width: The desired width of the output image.

    Returns:
        The target height that maintains the aspect ratio.
    """
    if img.width == 0:
        raise ValueError("Image width cannot be zero")

    aspect_ratio = img.height / img.width
    return int(target_width * aspect_ratio)


def pre_process_text(text: str) -> str:
    """
    Pre-processes the input text by cleaning and adding space separator.

    Args:
        text: The input text to be pre-processed.

    Returns:
        The cleaned text with space separator.

    Raises:
        ValueError: If text is empty after cleaning.
    """
    cleaned = clean_text(text)

    if not cleaned:
        raise ValueError("Text cannot be empty after cleaning")

    # Add single space for word separation
    # The gen_mosaic function will cycle through this using modulo
    return cleaned + " "


def pre_process_img(
    init_img: Image.Image,
    is_black_and_white: bool = True,
    contrast_factor: float = 1.5,
) -> Tuple[Image.Image, Image.Image]:
    """
    Pre-processes the input image by applying contrast and optional B&W filter.

    Args:
        init_img: The input image to be pre-processed.
        is_black_and_white: Whether to convert the image to black and white.
        contrast_factor: The factor by which to increase the contrast.

    Returns:
        Tuple of (processed_image, text_overlay_image).
    """
    # Convert to RGBA to ensure consistent color mode
    img = init_img.convert("RGBA")
    img = increase_contrast(img, contrast_factor)

    if is_black_and_white:
        img = apply_black_and_white_filter(img)

    # Create a new image for the text overlay with transparent background
    txt_img = Image.new("RGBA", img.size, (255, 255, 255, 0))

    return img, txt_img


def increase_contrast(img: Image.Image, factor: float = 1.5) -> Image.Image:
    """
    Increase the contrast of the image.

    Args:
        img: The input image.
        factor: The factor by which to increase the contrast.

    Returns:
        The image with adjusted contrast.
    """
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(factor)


def apply_black_and_white_filter(img: Image.Image) -> Image.Image:
    """
    Apply a black and white filter to the image.

    Args:
        img: The input image.

    Returns:
        The grayscale image.
    """
    return ImageEnhance.Color(img).enhance(0.0)


def gen_mosaic(
    img: Image.Image,
    text: str,
    font: ImageFont.FreeTypeFont,
    draw: ImageDraw.ImageDraw,
) -> None:
    """
    Generates a text mosaic by overlaying text onto the image.
    Uses numpy for faster pixel access.

    Args:
        img: The input image.
        text: The pre-processed text to overlay.
        font: The font used for drawing the text.
        draw: The drawing context for the text image.

    Raises:
        ValueError: If inputs are invalid.
    """
    if not text:
        raise ValueError("Text cannot be empty")

    char_width, char_height = get_charsize(font, draw)

    if char_width <= 0 or char_height <= 0:
        raise ValueError(f"Invalid character dimensions: {char_width}x{char_height}")

    text_position = 0
    max_text_len = len(text)

    # Add vertical padding to characters
    char_height_spaced = int(char_height * 1.5)
    x_offset = char_width // 2
    y_offset = char_height_spaced // 2

    # Convert image to numpy array for faster pixel access
    try:
        pixels = np.array(img)
    except Exception as e:
        logger.error(f"Failed to convert image to numpy array: {e}")
        # Fallback to slower getpixel method
        pixels = None

    # Generate mosaic
    try:
        for y in range(y_offset, img.size[1], char_height_spaced):
            for x in range(x_offset, img.size[0], char_width):
                # Bounds check
                if x >= img.size[0] or y >= img.size[1]:
                    continue

                # Get pixel color
                if pixels is not None:
                    # Fast numpy access
                    if y < pixels.shape[0] and x < pixels.shape[1]:
                        pixel = pixels[y, x]

                        # Check alpha channel for transparency
                        if img.mode == "RGBA" and pixel[3] == 0:
                            continue

                        pixel_color = tuple(pixel)
                    else:
                        continue
                else:
                    # Fallback to PIL getpixel
                    if img.mode == "RGBA":
                        r, g, b, a = img.getpixel((x, y))
                        if a == 0:
                            continue

                    pixel_color = img.getpixel((x, y))

                # Get character using modulo for efficient cycling
                char_to_draw = text[text_position % max_text_len]

                # Draw character
                draw.text((x, y), char_to_draw, font=font, fill=pixel_color)
                text_position += 1

    except Exception as e:
        logger.error(f"Error generating mosaic: {e}", exc_info=True)
        raise ValueError(f"Failed to generate mosaic: {e}")
