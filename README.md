# Text Mosaic Generator

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)](https://fastapi.tiangolo.com/)
[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange.svg)](https://aws.amazon.com/lambda/)
[![Terraform](https://img.shields.io/badge/Terraform-5.0+-purple.svg)](https://www.terraform.io/)

A production-grade serverless microservice that transforms images into artistic text-based mosaics. The service overlays customizable text onto images, with each character colored to match the underlying pixel colors, creating unique text-based visual representations.

## Features

- 🎨 **Artistic Text Mosaics**: Transform any image into a mosaic made entirely of text
- 🔧 **Customizable**: Adjust font size, contrast, colors, and dimensions
- 🖼️ **Format Support**: Works with PNG, JPEG, WebP, and other common formats
- ⚡ **High Performance**: Optimized with numpy and font caching for fast processing
- 🛡️ **Production-Ready**: Comprehensive security, error handling, and monitoring
- 📊 **Observable**: Structured logging, CloudWatch metrics, and X-Ray tracing
- 🚀 **Serverless**: AWS Lambda with auto-scaling and cost optimization
- 🌐 **RESTful API**: FastAPI with automatic documentation and validation

## Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/lemnispace/mosaic.git
cd mosaic

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r app/requirements.txt
pip install -r dev-requirements.txt

# Run locally
python scripts/start-fastapi.py
```

Access the API:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Quick Test

```bash
# Generate a mosaic
curl -X POST http://localhost:8000/ \
  -F "text=Hello World" \
  -F "width=800" \
  -F "file=@your-image.png" \
  --output mosaic.png
```

## Usage

### API Endpoints

#### `POST /` - Generate Mosaic

**Parameters:**
- `text` (required): Text to use for the mosaic
- `file` (required): Image file to process
- `width` (optional): Output width in pixels (default: 3840, range: 100-10000)
- `base_font_size` (optional): Base font size (default: 14, range: 6-100)
- `is_black_and_white` (optional): Convert to B&W (default: true)
- `contrast_factor` (optional): Contrast adjustment (default: 1.5, range: 0-5)

**Example:**
```bash
curl -X POST https://api.example.com/gen/mosaic/ \
  -F "text=The quick brown fox" \
  -F "width=1920" \
  -F "base_font_size=16" \
  -F "is_black_and_white=false" \
  -F "contrast_factor=2.0" \
  -F "file=@image.jpg" \
  -o output.png
```

**Response:**
- Success: PNG image stream (200)
- Validation error: JSON error message (400, 422)
- Server error: JSON error with request ID (500)

#### `GET /health` - Health Check

Returns service health status.

```bash
curl https://api.example.com/gen/mosaic/health
```

#### `GET /readiness` - Readiness Check

Verifies service can handle requests (checks font files, etc.).

```bash
curl https://api.example.com/gen/mosaic/readiness
```

### Python Client Example

```python
import requests

url = "http://localhost:8000/"

with open("image.png", "rb") as f:
    files = {"file": ("image.png", f, "image/png")}
    data = {
        "text": "Hello World",
        "width": 1920,
        "is_black_and_white": True,
        "contrast_factor": 1.5,
    }

    response = requests.post(url, files=files, data=data)

    if response.status_code == 200:
        with open("mosaic.png", "wb") as output:
            output.write(response.content)
        print("Mosaic generated successfully!")
    else:
        print(f"Error: {response.json()}")
```

### JavaScript/TypeScript Client Example

```typescript
async function generateMosaic(imageFile: File, text: string): Promise<Blob> {
  const formData = new FormData();
  formData.append("file", imageFile);
  formData.append("text", text);
  formData.append("width", "1920");
  formData.append("is_black_and_white", "true");

  const response = await fetch("https://api.example.com/gen/mosaic/", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message);
  }

  return response.blob();
}

// Usage
const imageFile = document.getElementById("imageInput").files[0];
const mosaicBlob = await generateMosaic(imageFile, "Your text here");
const url = URL.createObjectURL(mosaicBlob);
document.getElementById("result").src = url;
```

## Architecture

### System Overview

```
Client → API Gateway → Lambda (FastAPI) → Response
                          ├─ CloudWatch Logs
                          ├─ CloudWatch Metrics
                          ├─ CloudWatch Alarms
                          └─ X-Ray Traces
```

### Key Components

- **API Layer** (`app/main.py`): FastAPI application with CORS, validation, error handling
- **Service Layer** (`app/services/gen_text_mosaic.py`): Image processing and mosaic generation
- **Utilities** (`app/utils/`): Configuration, validation, helper functions
- **Infrastructure** (`terraform/`): AWS Lambda, API Gateway, CloudWatch

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

## Deployment

### Prerequisites

- Python 3.11+
- AWS CLI configured
- Terraform >= 1.0
- AWS SAM CLI (for local testing)

### Build and Deploy

```bash
# Build Lambda package
python scripts/build.py

# Initialize Terraform
cd terraform
terraform init

# Deploy to AWS
terraform apply
```

### Configuration

Set environment variables in `terraform/terraform.tfvars`:

```hcl
aws_region = "us-east-1"
stage = "Prod"
allow_origins = "https://your-domain.com"
root_path = "gen/mosaic"
log_level = "INFO"
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment guide.

## Development

### Project Structure

```
mosaic/
├── app/                    # Application code
│   ├── main.py            # FastAPI app & Lambda handler
│   ├── services/          # Business logic
│   ├── utils/             # Utilities
│   ├── fonts/             # TrueType fonts
│   └── requirements.txt   # Python dependencies
├── tests/                 # Test suite
│   ├── test_api_integration.py
│   ├── services/
│   └── utils/
├── terraform/             # Infrastructure as Code
│   ├── main.tf
│   ├── variables.tf
│   └── modules/
├── scripts/               # Build & dev scripts
│   ├── build.py
│   └── start-fastapi.py
├── .devcontainer/         # VS Code dev container
├── template.yaml          # SAM template
├── DEPLOYMENT.md          # Deployment guide
└── ARCHITECTURE.md        # Architecture docs
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api_integration.py

# Run integration tests only
pytest tests/test_api_integration.py -v
```

### Code Quality

```bash
# Format code
black app/ tests/

# Type checking
mypy app/

# Linting
pylint app/
```

## Monitoring

### CloudWatch Metrics

- **Invocations**: Total requests
- **Errors**: Failed requests
- **Duration**: Processing time
- **Throttles**: Rate-limited requests

### CloudWatch Alarms

Three alarms are configured:
1. **Errors**: >5 errors in 1 minute
2. **Duration**: Average >50 seconds (approaching 60s timeout)
3. **Throttles**: >5 throttles in 1 minute

### Logs

```bash
# View recent logs
aws logs tail /aws/lambda/TxtMosaicFunction --follow

# CloudWatch Insights query
fields @timestamp, request_id, duration_ms
| filter event = "mosaic_generated"
| stats avg(duration_ms), max(duration_ms) by bin(5m)
```

### X-Ray Tracing

View distributed traces in AWS X-Ray console for detailed request analysis.

## Performance

### Processing Times

| Image Size | Width | Typical Time | Memory Usage |
|------------|-------|--------------|--------------|
| Small      | 200px | 1-2s        | ~50MB        |
| Medium     | 1080px| 5-10s       | ~150MB       |
| Large      | 3840px| 15-30s      | ~300MB       |
| Max        | 10000px| 45-60s     | ~400MB       |

### Optimizations

- ✅ Font caching (LRU cache)
- ✅ Numpy pixel access (2-5x faster)
- ✅ Efficient text cycling (O(1) memory)
- ✅ Explicit memory management
- ✅ Increased Lambda memory (1024MB)

## Security

### Input Validation

- ✅ File size limits (10MB max)
- ✅ Image dimension limits (10,000px max)
- ✅ Decompression bomb detection
- ✅ Content-type validation
- ✅ Parameter range validation

### CORS Security

- ✅ Configurable origins (no wildcard in production)
- ✅ Credentials only with specific origins
- ✅ Explicit allowed methods

### Resource Limits

- ✅ Lambda timeout: 60 seconds
- ✅ Lambda memory: 1024MB
- ✅ Concurrent executions: 10 (cost protection)
- ✅ Memory estimation before processing

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI schema: `http://localhost:8000/openapi.json`

## Troubleshooting

### Common Issues

**Lambda Timeout (502)**
- Reduce `width` parameter
- Use smaller images
- Check CloudWatch duration metrics

**Out of Memory**
- Reduce image dimensions
- Lower `width` parameter
- Increase Lambda memory in Terraform

**CORS Errors**
- Verify `ALLOWED_ORIGINS` environment variable
- Check protocol (http vs https)
- Ensure proper domain configuration

**413 File Too Large**
- Compress image before upload
- Reduce image dimensions
- Maximum size is 10MB

See [DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting) for detailed troubleshooting guide.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Open an issue on GitHub
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment help
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for system details

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Image processing powered by [Pillow](https://python-pillow.org/)
- Serverless deployment with [AWS Lambda](https://aws.amazon.com/lambda/)
- Infrastructure managed by [Terraform](https://www.terraform.io/)
- Font: [Noto Sans Mono](https://fonts.google.com/noto/specimen/Noto+Sans+Mono)

---

Made with ❤️ by LemniSpace
