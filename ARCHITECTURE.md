# Architecture Documentation

## Overview

The Text Mosaic Service is a serverless microservice built on AWS Lambda that transforms images into artistic text-based mosaics. The service overlays user-provided text onto images, with each character colored to match the underlying pixel color.

## System Architecture

```
┌─────────────┐
│   Client    │
│  (Browser/  │
│    API)     │
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────────────────────────┐
│   API Gateway HTTP API          │
│   - CORS handling               │
│   - Request routing             │
│   - Throttling                  │
└──────┬──────────────────────────┘
       │ Proxy
       ▼
┌─────────────────────────────────┐
│   AWS Lambda                    │
│   - Python 3.11                 │
│   - 1024MB memory               │
│   - 60s timeout                 │
│   - X-Ray tracing               │
└──────┬──────────────────────────┘
       │
       ├─────► CloudWatch Logs
       ├─────► CloudWatch Metrics
       ├─────► X-Ray Traces
       └─────► CloudWatch Alarms
```

## Component Architecture

### 1. API Layer (`app/main.py`)

**Responsibilities:**
- HTTP request handling
- Request validation
- CORS management
- Request ID tracking
- Error handling
- Response formatting
- Health checks

**Key Components:**
- **FastAPI Application**: Async web framework
- **Mangum Adapter**: AWS Lambda ↔ ASGI bridge
- **CORS Middleware**: Cross-origin request handling
- **Request ID Middleware**: Distributed tracing
- **Exception Handlers**: Global error management

**Endpoints:**
- `POST /`: Generate text mosaic
- `GET /health`: Health check
- `GET /readiness`: Readiness check

### 2. Service Layer (`app/services/gen_text_mosaic.py`)

**Responsibilities:**
- Image processing pipeline
- Text mosaic generation algorithm
- Font management and caching
- Memory estimation and limits
- Performance optimization

**Processing Pipeline:**
```
Input Image → Resize → Enhance Contrast → B&W Filter → Text Overlay → Output PNG
```

**Key Functions:**

1. **`gen_text_mosaic()`**: Main orchestration
   - Validates inputs
   - Estimates memory requirements
   - Coordinates processing pipeline
   - Manages resource cleanup

2. **`get_font()`**: Resolution-based font scaling
   - Caches font objects (LRU cache, size=32)
   - Scales font based on image width
   - Supports 480px to 7200px+ widths

3. **`gen_mosaic()`**: Core algorithm
   - Uses numpy for fast pixel access
   - Iterates grid positions
   - Maps pixel colors to characters
   - Handles transparency

### 3. Utility Layer (`app/utils/`)

#### `config.py`
- Environment variable management
- Configuration validation
- CORS origin validation
- Logging setup

#### `util.py`
- Path resolution
- Text cleaning/normalization
- Character size calculation
- Image to bytes conversion

#### `server_util.py`
- Image file validation and loading
- Security checks (size, dimensions, decompression bombs)
- ASGI handler creation
- Lambda stage extraction

## Data Flow

### Request Flow

1. **Client Request**
   ```
   POST / HTTP/1.1
   Content-Type: multipart/form-data

   text: "Hello World"
   width: 3840
   file: image.png
   ```

2. **API Gateway**
   - Routes to Lambda
   - Applies throttling
   - Adds stage context

3. **Lambda Handler** (`handler()`)
   - Receives event/context
   - Creates ASGI handler
   - Invokes FastAPI app

4. **Request Middleware**
   - Generates request ID (UUID)
   - Starts timing
   - Sets context variables

5. **Endpoint Handler** (`mosaic()`)
   - Validates parameters
   - Loads and validates image
   - Generates mosaic
   - Returns PNG stream

6. **Response Middleware**
   - Adds request ID header
   - Logs performance metrics
   - Returns to Lambda handler

7. **Lambda Handler**
   - Logs invocation details
   - Returns response to API Gateway

8. **API Gateway**
   - Adds CORS headers
   - Returns to client

### Image Processing Flow

```python
# 1. Load and validate
image = load_image_file(file)
  ├─ Check content-type
  ├─ Check file size (<10MB)
  ├─ Verify image integrity
  ├─ Check dimensions (<10,000px)
  └─ Detect decompression bombs

# 2. Estimate memory
memory_mb = (width × height × 4 bytes × 3 images) / 1MB
if memory_mb > 400MB: raise ValueError

# 3. Resize
resized = image.resize((target_width, target_height))

# 4. Pre-process
img_rgba = resized.convert("RGBA")
img_contrast = increase_contrast(img_rgba, factor)
if is_bw: img_bw = apply_black_and_white_filter(img_contrast)

# 5. Generate mosaic
for y in grid_y:
  for x in grid_x:
    pixel_color = img[y, x]  # Numpy array access
    char = text[pos % len(text)]
    draw.text((x, y), char, fill=pixel_color)

# 6. Convert to PNG bytes
img_bytes = image_to_bytes(mosaic, format="PNG")

# 7. Return stream
return StreamingResponse(img_bytes, media_type="image/png")
```

## Security Architecture

### Input Validation

1. **File Upload Security**
   - Content-type validation
   - File size limits (10MB max)
   - Image dimension limits (10,000px max)
   - Magic byte validation via `Image.verify()`
   - Decompression bomb detection

2. **Parameter Validation**
   - FastAPI schema validation
   - Range checks (width: 100-10,000px)
   - Type validation
   - Empty string checks

3. **CORS Security**
   - Configurable origins (no wildcard in production)
   - Credentials only with specific origins
   - Explicit methods (POST, GET, OPTIONS)

### Resource Limits

1. **Lambda Limits**
   - Timeout: 60 seconds
   - Memory: 1024MB
   - Concurrent executions: 10 (prevents runaway costs)

2. **Application Limits**
   - Max image memory: 400MB (leaves buffer for overhead)
   - Max upload size: 10MB
   - Max dimensions: 10,000 × 10,000px

3. **API Gateway Limits**
   - Request timeout: 30 seconds
   - Payload size: 10MB
   - Throttling: Configurable via usage plans

## Performance Optimizations

### 1. Font Caching
```python
@lru_cache(maxsize=32)
def _load_font(font_size: int):
    return ImageFont.truetype(font_path, font_size)
```
- Caches up to 32 font sizes
- Eliminates repeated file I/O
- ~100ms savings per request

### 2. Numpy Pixel Access
```python
pixels = np.array(img)
for y, x in grid:
    color = pixels[y, x]  # 10-100x faster than getpixel()
```
- 2-5x faster for large images
- Batch pixel access
- Fallback to `getpixel()` if numpy fails

### 3. Efficient Text Cycling
```python
char = text[position % len(text)]  # Modulo instead of huge string
```
- Eliminates multi-MB string generation
- O(1) memory instead of O(n)
- Reduces GC pressure

### 4. Explicit Memory Management
```python
del img, resized, draw  # Explicit cleanup
```
- Reduces peak memory usage
- Helps Python GC
- Critical for Lambda memory limits

### 5. Increased Lambda Memory
- 1024MB vs 512MB
- More CPU allocated proportionally
- Faster image processing

## Monitoring Architecture

### 1. Structured Logging

All logs use JSON format for easy parsing:
```json
{
  "request_id": "uuid",
  "event": "mosaic_generated",
  "output_size": "3840x2160",
  "generation_time_ms": 1234.56
}
```

**Log Events:**
- `request_completed`: Every request
- `mosaic_request_received`: Request start
- `image_loaded`: Image validation done
- `mosaic_generated`: Processing complete
- `mosaic_generation_failed`: Errors
- `lambda_invocation`: Lambda entry/exit

### 2. CloudWatch Metrics

**Lambda Metrics (automatic):**
- Invocations
- Errors
- Duration
- Throttles
- Concurrent Executions
- Iterator Age (for streams)

**Custom Metrics (via logs):**
- Request count by endpoint
- Generation time distribution
- Image size distribution
- Error types

### 3. CloudWatch Alarms

1. **Error Alarm**
   - Metric: Errors > 5 in 1 minute
   - Use: Detect sudden failures

2. **Duration Alarm**
   - Metric: Avg duration > 50 seconds
   - Use: Detect performance degradation

3. **Throttle Alarm**
   - Metric: Throttles > 5 in 1 minute
   - Use: Detect capacity issues

### 4. X-Ray Tracing

- Full request traces
- Service map visualization
- Subsegments for key operations
- Error and fault tracking
- Performance bottleneck identification

## Scalability

### Horizontal Scaling
- **Lambda Auto-scaling**: Automatic based on traffic
- **Concurrent Limit**: 10 (configurable)
- **Cold Start**: ~2-5 seconds (FastAPI + dependencies)
- **Warm Invocations**: ~0-500ms overhead

### Capacity Planning

**Single Lambda Capacity:**
- Memory: 1024MB
- Timeout: 60s
- Theoretical max: 1 request/60s

**10 Concurrent Lambdas:**
- Max throughput: ~10 requests/60s
- Burst: 10 simultaneous
- Cost protection: Limited concurrency

**Scaling Beyond 10:**
- Increase `reserved_concurrent_executions`
- Monitor costs
- Consider adding API Gateway throttling

### Performance Characteristics

| Image Size | Width | Processing Time | Memory Usage |
|------------|-------|-----------------|--------------|
| Small      | 200px | 1-2s           | ~50MB        |
| Medium     | 1080px| 5-10s          | ~150MB       |
| Large      | 3840px| 15-30s         | ~300MB       |
| Max        | 10000px| 45-60s        | ~400MB       |

## Deployment Architecture

### Infrastructure as Code (Terraform)

```
terraform/
├── main.tf           # Lambda, CloudWatch, alarms
├── variables.tf      # Input variables
├── outputs.tf        # Output values
└── modules/
    └── routes/
        └── main.tf   # API Gateway integration
```

**Resources Managed:**
- Lambda function
- CloudWatch log group (14-day retention)
- CloudWatch alarms (3x)
- API Gateway integration
- API Gateway route
- Lambda permissions
- S3 deployment artifact

### Build Process

```bash
build.py → pip install → copy code → .aws-sam/build/
         → terraform package → S3 upload → Lambda update
```

### Deployment Pipeline

1. **Local Development**: FastAPI dev server
2. **Local Testing**: SAM local
3. **Unit Tests**: pytest
4. **Integration Tests**: TestClient
5. **Build**: Package Lambda
6. **Plan**: Terraform plan
7. **Deploy**: Terraform apply
8. **Smoke Test**: Health check
9. **Monitor**: CloudWatch/X-Ray

## Error Handling Strategy

### 1. Validation Errors (400, 422)
- Input validation failures
- Return clear error messages
- Log for debugging
- Don't retry

### 2. Server Errors (500)
- Unexpected exceptions
- Log full stack trace
- Return generic message
- Include request ID

### 3. Lambda Timeout (502)
- Processing exceeded 60s
- Log partial progress
- Client should reduce image size
- Monitor duration metrics

### 4. Throttling (429)
- Concurrent limit reached
- Client should retry with backoff
- Monitor throttle metrics
- Consider increasing limit

## Testing Strategy

### 1. Unit Tests
- Individual functions
- Mock external dependencies
- Fast execution (<1s)
- Located in `tests/utils/`, `tests/services/`

### 2. Integration Tests
- Full API endpoints
- Real image processing
- TestClient (no AWS)
- Located in `tests/test_api_integration.py`

### 3. Edge Case Tests
- Boundary values
- Invalid inputs
- Unicode/special characters
- Large files
- Corrupted images

### 4. Performance Tests
- Large images
- Measure latency
- Memory profiling
- Identify bottlenecks

## Future Enhancements

### Potential Improvements

1. **Caching Layer**
   - Redis/ElastiCache for repeated requests
   - S3 for generated images
   - CloudFront CDN

2. **Async Processing**
   - SQS queue for long-running jobs
   - S3 event notifications
   - Webhook callbacks

3. **Advanced Features**
   - Multiple font options
   - Color palettes
   - Text effects (shadow, outline)
   - Batch processing

4. **API Enhancements**
   - Authentication (API keys, OAuth)
   - Rate limiting per user
   - Webhook support
   - GraphQL interface

5. **Observability**
   - Custom CloudWatch dashboards
   - Application Insights
   - Distributed tracing improvements
   - Cost tracking

## Appendix

### Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Runtime | Python | 3.11 |
| Web Framework | FastAPI | 0.109.0 |
| ASGI Server | Uvicorn | 0.27.0 |
| Lambda Adapter | Mangum | 0.17.0 |
| Image Processing | Pillow | 10.2.0 |
| Numerical | NumPy | 1.26.3 |
| Infrastructure | Terraform | 5.0+ |
| Compute | AWS Lambda | - |
| API | API Gateway v2 | - |
| Monitoring | CloudWatch | - |
| Tracing | X-Ray | - |

### Glossary

- **ASGI**: Asynchronous Server Gateway Interface
- **Mosaic**: Text-based representation of an image
- **Lambda Cold Start**: Initial invocation overhead
- **X-Ray**: AWS distributed tracing service
- **CloudWatch**: AWS monitoring and logging service
- **CORS**: Cross-Origin Resource Sharing
- **Decompression Bomb**: Malicious file that expands to huge size
- **Request ID**: UUID for tracking requests

### References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Pillow (PIL) Documentation](https://pillow.readthedocs.io/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/)
