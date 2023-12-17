from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from utils.util import get_absolute_path, clean_text, get_charsize


def gen_text_mosaic(text: str, img: Image, target_width=3840):
    """
    Generate a text mosaic image by repeating the given text to fill the image.
    The output image will be resized to the target width while maintaining the aspect ratio.

    Args:
        text (str): The text to be repeated in the text mosaic.
        img (PIL.Image.Image): The input image on which the text mosaic will be generated.
        target_width (int, optional): The desired width of the output image. Defaults to 3840.

    Returns:
        PIL.Image.Image: The generated text mosaic image.
    """
    # Resize image to improve resolution
    target_height = get_target_height(img, target_width)
    img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

    font = get_font(target_width)
    # Pre-process the image (apply edge enhancement)
    image, edge_img, txt_img = pre_process_img(img)
    # Create a drawing context for the text image
    draw = ImageDraw.Draw(txt_img)
    # Pre-process the text
    text = pre_process_text(draw, text, font, target_width, target_height)
    # Generate the text mosaic
    gen_mosaic(image, edge_img, text, font, draw)

    # Return the text image
    return txt_img


def get_font(img_width: int):
    # determine the best font size based on the target image size
    # we'll use resolution based scaling to determine the font size
    default_font_size = 8
    if img_width >= 2160:
        font_size = default_font_size * 3
    elif img_width >= 1080:
        font_size = default_font_size * 1.5
    elif img_width <= 480:
        font_size = default_font_size * 0.5
    elif img_width <= 720:
        font_size = default_font_size * 0.75
    else:
        font_size = default_font_size
    font_path = str(get_absolute_path("../fonts/RobotoMono-Regular.ttf"))
    font = ImageFont.truetype(font_path, int(font_size))

    return font


def get_target_height(img, target_width):
    """
    Get the target height of the output image based on the target width and the aspect ratio of the input image.

    Args:
        img (PIL.Image.Image): The input image.
        target_width (int): The desired width of the output image.

    Returns:
        int: The target height of the output image.
    """
    aspect_ratio = img.height / img.width
    return int(target_width * aspect_ratio)


def pre_process_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    target_width: int,
    target_height: int,
):
    """
    Pre-processes the input text by removing any special characters.

    Args:
        draw (PIL.ImageDraw.ImageDraw): The drawing context for the text image.
        text (str): The input text to be pre-processed.
        font (PIL.ImageFont.ImageFont): The font used for drawing the text.
        target_width (int): The width of the target image.
        target_height (int): The height of the target image.

    Returns:
        str: The pre-processed text.
    """
    char_width, char_height = get_charsize(font, draw)
    approx_chars_per_line = target_width // char_width
    approx_number_of_lines = target_height // char_height
    total_chars_needed = approx_chars_per_line * approx_number_of_lines
    text_repetitions_needed = total_chars_needed // len(text) + 1
    #
    # Ensure text is padded with spaces and repeated
    text = " ".join([clean_text(text)] * text_repetitions_needed) + " "

    return text


def pre_process_img(init_img):
    """
    Pre-processes the input image by applying an edge enhancement filter.

    Args:
        init_img (PIL.Image.Image): The input image to be pre-processed.

    Returns:
        Tuple[PIL.Image.Image, PIL.Image.Image, PIL.Image.Image]: The pre-processed image, edge image, and text image.
    """
    # Convert to RGBA if necessary to ensure it's in the correct mode
    img = init_img.convert("RGBA")
    img = increase_contrast(img)
    edge_img = apply_edge_detection(img)
    # Create a new image for the text overlay with a transparent background
    txt_img = Image.new("RGBA", img.size, (255, 255, 255, 0))

    return img, edge_img, txt_img


def increase_contrast(img):
    """
    Increase the contrast of the image to make the subject more pronounced.

    Args:
        img (PIL.Image.Image): The input image.

    Returns:
        PIL.Image.Image: The image with increased contrast.
    """
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(2.0)  # Increase contrast; adjust the factor as needed


def apply_edge_detection(img):
    """
    Apply edge detection filter to the image.

    Args:
        img (PIL.Image.Image): The input image.

    Returns:
        PIL.Image.Image: The image with edge detection applied.
    """
    edges = img.filter(ImageFilter.FIND_EDGES)
    return increase_contrast(edges)


def gen_mosaic(
    img: Image,
    edge_img: Image,
    text: str,
    font: ImageFont.FreeTypeFont,
    draw: ImageDraw,
):
    """
    Generates a text mosaic by overlaying the given text onto the image.

    Args:
        img (PIL.Image.Image): The input image.
        edge_img (PIL.Image.Image): The image with edge detection applied.
        text (str): The text to be overlayed on the image.
        font (PIL.ImageFont.ImageFont): The font used for drawing the text.
        draw (PIL.ImageDraw.ImageDraw): The drawing context for the text image.
    """
    char_width, char_height = get_charsize(font, draw)
    text_position = 0
    max_text_len = len(text)

    # add padding to the character
    char_height = int(char_height * 1.5)

    # Use the edge image for edge detection but the original image for color
    for y in range(0, img.size[1], char_height):
        for x in range(0, img.size[0], char_width):
            if text_position >= max_text_len:
                text_position = 0

            # Use color from the original image, not the edge-detected image
            pixel_color = img.getpixel((x, y))
            edge_pixel_value = edge_img.getpixel((x, y))
            is_edge = (
                max(edge_pixel_value) > 128
            )  # Determine if the pixel is part of an edge
            text_color = pixel_color if not is_edge else (0, 0, 0, 255)
            draw.text((x, y), text[text_position], font=font, fill=text_color)
            text_position += 1
