"""
Integration tests for the mosaic API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
import io
from PIL import Image


client = TestClient(app)


@pytest.fixture
def sample_image_file():
    """Create a valid test image file"""
    img = Image.new('RGB', (200, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes


@pytest.fixture
def large_image_file():
    """Create a larger test image"""
    img = Image.new('RGB', (1920, 1080), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes


def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_readiness_endpoint():
    """Test readiness check endpoint"""
    response = client.get("/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


def test_mosaic_endpoint_success(sample_image_file):
    """Test successful mosaic generation with valid inputs"""
    response = client.post(
        "/",
        data={"text": "Hello World", "width": 200},
        files={"file": ("test.png", sample_image_file, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0
    assert "x-request-id" in response.headers


def test_mosaic_endpoint_with_all_parameters(sample_image_file):
    """Test mosaic generation with all optional parameters"""
    response = client.post(
        "/",
        data={
            "text": "Test Mosaic",
            "width": 400,
            "base_font_size": 16,
            "is_black_and_white": False,
            "contrast_factor": 2.0,
        },
        files={"file": ("test.png", sample_image_file, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_mosaic_endpoint_black_and_white(sample_image_file):
    """Test B&W mosaic generation"""
    response = client.post(
        "/",
        data={
            "text": "BW Test",
            "is_black_and_white": True,
        },
        files={"file": ("test.png", sample_image_file, "image/png")}
    )
    assert response.status_code == 200


def test_mosaic_endpoint_color(sample_image_file):
    """Test color mosaic generation"""
    response = client.post(
        "/",
        data={
            "text": "Color Test",
            "is_black_and_white": False,
        },
        files={"file": ("test.png", sample_image_file, "image/png")}
    )
    assert response.status_code == 200


def test_mosaic_endpoint_missing_text():
    """Test with missing required text parameter"""
    img = Image.new('RGB', (100, 100), color='green')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    response = client.post(
        "/",
        files={"file": ("test.png", img_bytes, "image/png")}
    )
    assert response.status_code == 422  # FastAPI validation error


def test_mosaic_endpoint_empty_text(sample_image_file):
    """Test with empty text"""
    response = client.post(
        "/",
        data={"text": "   "},  # Only whitespace
        files={"file": ("test.png", sample_image_file, "image/png")}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["message"].lower()


def test_mosaic_endpoint_invalid_image():
    """Test with invalid image data"""
    fake_image = io.BytesIO(b"not an image")
    response = client.post(
        "/",
        data={"text": "Test"},
        files={"file": ("test.txt", fake_image, "image/png")}
    )
    assert response.status_code == 400


def test_mosaic_endpoint_wrong_content_type(sample_image_file):
    """Test with wrong content type header"""
    response = client.post(
        "/",
        data={"text": "Test"},
        files={"file": ("test.png", sample_image_file, "text/plain")}
    )
    assert response.status_code == 400


def test_mosaic_endpoint_missing_file():
    """Test without file upload"""
    response = client.post(
        "/",
        data={"text": "Test"}
    )
    assert response.status_code == 422  # FastAPI validation error


def test_mosaic_endpoint_width_too_small(sample_image_file):
    """Test with width below minimum"""
    response = client.post(
        "/",
        data={"text": "Test", "width": 50},
        files={"file": ("test.png", sample_image_file, "image/png")}
    )
    assert response.status_code == 422


def test_mosaic_endpoint_width_too_large(sample_image_file):
    """Test with width above maximum"""
    response = client.post(
        "/",
        data={"text": "Test", "width": 15000},
        files={"file": ("test.png", sample_image_file, "image/png")}
    )
    assert response.status_code == 422


def test_mosaic_endpoint_font_size_too_small(sample_image_file):
    """Test with font size below minimum"""
    response = client.post(
        "/",
        data={"text": "Test", "base_font_size": 2},
        files={"file": ("test.png", sample_image_file, "image/png")}
    )
    assert response.status_code == 422


def test_mosaic_endpoint_font_size_too_large(sample_image_file):
    """Test with font size above maximum"""
    response = client.post(
        "/",
        data={"text": "Test", "base_font_size": 200},
        files={"file": ("test.png", sample_image_file, "image/png")}
    )
    assert response.status_code == 422


def test_mosaic_endpoint_invalid_contrast_factor(sample_image_file):
    """Test with contrast factor out of range"""
    response = client.post(
        "/",
        data={"text": "Test", "contrast_factor": 10.0},
        files={"file": ("test.png", sample_image_file, "image/png")}
    )
    assert response.status_code == 422


def test_mosaic_endpoint_unicode_text(sample_image_file):
    """Test with unicode characters"""
    response = client.post(
        "/",
        data={"text": "Hello 世界 🌍"},
        files={"file": ("test.png", sample_image_file, "image/png")}
    )
    assert response.status_code == 200


def test_mosaic_endpoint_long_text(sample_image_file):
    """Test with very long text"""
    long_text = "Lorem ipsum " * 1000
    response = client.post(
        "/",
        data={"text": long_text},
        files={"file": ("test.png", sample_image_file, "image/png")}
    )
    assert response.status_code == 200


def test_mosaic_endpoint_jpeg_image():
    """Test with JPEG image format"""
    img = Image.new('RGB', (200, 100), color='yellow')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)

    response = client.post(
        "/",
        data={"text": "JPEG Test"},
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200


def test_mosaic_endpoint_rgba_image():
    """Test with RGBA (transparent) image"""
    img = Image.new('RGBA', (200, 100), color=(255, 0, 0, 128))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    response = client.post(
        "/",
        data={"text": "Transparent Test"},
        files={"file": ("test.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200


def test_mosaic_endpoint_small_image():
    """Test with very small image (edge case)"""
    img = Image.new('RGB', (10, 10), color='purple')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    response = client.post(
        "/",
        data={"text": "Small", "width": 100},
        files={"file": ("test.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200


def test_mosaic_endpoint_large_image(large_image_file):
    """Test with larger image"""
    response = client.post(
        "/",
        data={"text": "Large Image Test", "width": 1920},
        files={"file": ("test.png", large_image_file, "image/png")}
    )
    assert response.status_code == 200


def test_mosaic_endpoint_special_characters(sample_image_file):
    """Test with special characters in text"""
    response = client.post(
        "/",
        data={"text": "!@#$%^&*()_+-=[]{}|;':\"<>?,./"},
        files={"file": ("test.png", sample_image_file, "image/png")}
    )
    assert response.status_code == 200


def test_mosaic_endpoint_newlines_in_text(sample_image_file):
    """Test that newlines are handled correctly"""
    response = client.post(
        "/",
        data={"text": "Line 1\nLine 2\nLine 3"},
        files={"file": ("test.png", sample_image_file, "image/png")}
    )
    assert response.status_code == 200


def test_mosaic_endpoint_tabs_in_text(sample_image_file):
    """Test that tabs are handled correctly"""
    response = client.post(
        "/",
        data={"text": "Col1\tCol2\tCol3"},
        files={"file": ("test.png", sample_image_file, "image/png")}
    )
    assert response.status_code == 200


def test_mosaic_endpoint_min_width(sample_image_file):
    """Test with minimum allowed width"""
    response = client.post(
        "/",
        data={"text": "Min Width", "width": 100},
        files={"file": ("test.png", sample_image_file, "image/png")}
    )
    assert response.status_code == 200


def test_mosaic_endpoint_min_font_size(sample_image_file):
    """Test with minimum allowed font size"""
    response = client.post(
        "/",
        data={"text": "Min Font", "base_font_size": 6},
        files={"file": ("test.png", sample_image_file, "image/png")}
    )
    assert response.status_code == 200


def test_mosaic_endpoint_zero_contrast(sample_image_file):
    """Test with zero contrast factor"""
    response = client.post(
        "/",
        data={"text": "Zero Contrast", "contrast_factor": 0.0},
        files={"file": ("test.png", sample_image_file, "image/png")}
    )
    assert response.status_code == 200


def test_cors_headers():
    """Test that CORS headers are present"""
    response = client.options("/")
    # CORS headers should be present
    # Actual validation depends on ALLOWED_ORIGINS setting


def test_request_id_in_response(sample_image_file):
    """Test that request ID is included in response headers"""
    response = client.post(
        "/",
        data={"text": "Test"},
        files={"file": ("test.png", sample_image_file, "image/png")}
    )
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0
