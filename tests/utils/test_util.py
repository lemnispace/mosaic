import pytest
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from app.utils.util import (
    get_absolute_path,
    clean_text,
    get_charsize,
)
import os


# Fixture to create a test file
@pytest.fixture
def test_file(tmp_path) -> Path:
    test_file_path = tmp_path / "test_file.txt"
    test_file_path.write_text("Test content")
    return test_file_path


def test_get_absolute_path_nonexistent():
    with pytest.raises(FileNotFoundError):
        get_absolute_path("nonexistent_file.txt")


def test_get_absolute_path_exists(test_file):
    absolute_path = get_absolute_path(str(test_file.name), base_path=test_file.parent)
    assert absolute_path == test_file


# # Test clean_text function
def test_clean_text():
    assert clean_text("This is a test") == "This is a test"
    assert clean_text(" This   is  a   test ") == "This is a test"
    assert clean_text("\nThis\tis\na test\n") == "This is a test"


# Test get_charsize function
def test_get_charsize():
    # Create an image to get a drawing context
    img = Image.new("RGB", (100, 100))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=10)  # uses the Aileron Regular font

    # Test with default character
    char_width_a, char_height_a = get_charsize(font, draw, char="A")
    assert char_width_a == 7
    assert char_height_a == 8

    # Test with different character
    char_width_w, char_height_w = get_charsize(font, draw, char="W")
    assert char_width_w == 10
    assert char_height_w == char_height_a
    # Ensure width of 'W' is greater than width of 'I'
    char_width_i, char_height_i = get_charsize(font, draw, char="I")
    assert char_width_w > char_width_i
    assert char_height_i == char_height_w
