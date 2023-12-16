from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance


def gen_text_mosaic(text, img, target_width=3840):
    """
    Generate a text mosaic image by repeating the given text to fill the image.
    The output image will be resized to the target width while maintaining the aspect ratio.
    """
    # Resize image to improve resolution
    aspect_ratio = img.height / img.width
    target_height = int(target_width * aspect_ratio)
    img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

    font = ImageFont.load_default()
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


def pre_process_text(draw, text, font, target_width, target_height):
    """
    Pre-processes the input text by removing any special characters.
    """
    char_size = draw.textbbox((0, 0), "A", font=font)
    char_width = char_size[2] - char_size[0]
    char_height = char_size[3] - char_size[1]
    approx_chars_per_line = target_width // char_width
    approx_number_of_lines = target_height // char_height
    total_chars_needed = approx_chars_per_line * approx_number_of_lines
    text_repetitions_needed = total_chars_needed // len(text) + 1

    # Ensure text is padded with spaces and repeated
    text = " ".join([text.strip()] * text_repetitions_needed) + " "

    return text


def pre_process_img(init_img):
    """
    Pre-processes the input image by applying an edge enhancement filter.
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
    """
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(2.0)  # Increase contrast; adjust the factor as needed


def apply_edge_detection(img):
    edges = img.filter(ImageFilter.FIND_EDGES)
    return increase_contrast(edges)


def gen_mosaic(img, edge_img, text, font, draw):
    """
    Generates a text mosaic by overlaying the given text onto the image.
    """
    char_size = draw.textbbox((0, 0), "A", font=font)
    char_width = char_size[2] - char_size[0]
    char_height = char_size[3] - char_size[1]
    text_position = 0
    max_text_len = len(text)

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
