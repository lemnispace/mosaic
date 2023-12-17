import pytest
from PIL import Image, ImageFont, ImageDraw
from app.services.gen_text_mosaic import (
    get_target_height,
    pre_process_text,
    gen_text_mosaic,
)

# Constants for the test
TEST_TARGET_WIDTH = 100
TEST_TEXT = "Test"


# Fixture for creating an image
@pytest.fixture
def sample_image():
    img = Image.new("RGB", (200, 100), color="white")
    return img


# Fixture for creating a font object
@pytest.fixture
def sample_font():
    return ImageFont.load_default(size=10)


# Fixture for creating a draw object
@pytest.fixture
def sample_draw(sample_image):
    draw = ImageDraw.Draw(sample_image)
    return draw


def test_get_target_height(sample_image):
    target_height = get_target_height(sample_image, TEST_TARGET_WIDTH)
    assert (
        target_height == (TEST_TARGET_WIDTH * sample_image.height) // sample_image.width
    )


def test_pre_process_text(sample_draw, sample_font):
    processed_text = pre_process_text(
        sample_draw, TEST_TEXT, sample_font, TEST_TARGET_WIDTH, 50
    )
    assert isinstance(processed_text, str)
    assert (
        TEST_TEXT in processed_text
    )  # Check if the TEST_TEXT is actually in the processed text


def test_gen_text_mosaic(sample_image):
    result_img = gen_text_mosaic(TEST_TEXT, sample_image, TEST_TARGET_WIDTH)
    assert result_img.size[0] == TEST_TARGET_WIDTH
    assert result_img.size[1] == get_target_height(sample_image, TEST_TARGET_WIDTH)


# Test that the text is actually drawn on the image could be complex since we would need to analyze the image content.
# One approach could be to check the pixel values at expected text positions to see if they have changed from the base image.
