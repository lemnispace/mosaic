import pytest
from PIL import Image, ImageFont, ImageDraw
from app.services.gen_text_mosaic import (
    get_target_height,
    pre_process_text,
    gen_text_mosaic,
    get_font,
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


def test_get_font():
    tests = [
        {"default_font_size": 10, "img_width": 2048, "expected_font_size": 15},
        {"default_font_size": 10, "img_width": 512, "expected_font_size": 7},
        {"default_font_size": 123, "img_width": 1024, "expected_font_size": 123},
        {"default_font_size": 10, "img_width": 1080, "expected_font_size": 15},
        {"default_font_size": 10, "img_width": 200, "expected_font_size": 5},
        {"default_font_size": 10, "img_width": 4080, "expected_font_size": 30},
    ]
    for test in tests:
        font = get_font(test["img_width"], test["default_font_size"])
        assert isinstance(font, ImageFont.FreeTypeFont)
        assert font.size == test["expected_font_size"]
