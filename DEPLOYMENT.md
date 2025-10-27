# Deployment Guide

## Table of Contents
- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Building for Deployment](#building-for-deployment)
- [Deploying to AWS](#deploying-to-aws)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools
- **Python 3.11+**
- **AWS CLI** configured with appropriate credentials
- **Terraform >= 1.0**
- **AWS SAM CLI** (for local testing)
- **Docker** (for dev container or SAM local testing)

### AWS Resources
- S3 bucket for Terraform state (`lemnispace-terraform-state`)
- DynamoDB table for Terraform locking (`terraform-state-lock`)
- IAM role for Lambda execution
- API Gateway HTTP API

### Permissions Required
- Lambda: Create, Update, Delete functions
- CloudWatch: Create log groups and alarms
- S3: Upload deployment packages
- API Gateway: Configure routes and integrations
- IAM: Attach execution policies

## Local Development

### Option 1: Dev Container (Recommended)
1. Open project in VS Code
2. Click "Reopen in Container" when prompted
3. Container includes all dependencies

### Option 2: Manual Setup
```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r app/requirements.txt
pip install -r dev-requirements.txt
```

### Running Locally
```bash
# Start FastAPI development server
python scripts/start-fastapi.py

# Or use uvicorn directly
cd app
uvicorn main:app --reload --port 8000
```

### Access API
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Testing Locally
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api_integration.py

# Run with verbose output
pytest -v
```

### Local Testing with SAM
```bash
# Build Lambda package
python scripts/build.py

# Start SAM local API
sam build
sam local start-api --port 3000

# Test endpoint
curl -X POST http://localhost:3000/gen/mosaic/ \
  -F "text=Hello World" \
  -F "file=@test-image.png" \
  --output result.png
```

## Building for Deployment

### Build Lambda Package
```bash
# Build deployment package
python scripts/build.py

# Or with custom function name
python scripts/build.py --lambda-name MyMosaicFunction

# Output: .aws-sam/build/MosaicFunction/
```

### Verify Build
```bash
# Check build directory
ls -lh .aws-sam/build/MosaicFunction/

# Should contain:
# - All Python dependencies
# - Application code (main.py, services/, utils/)
# - Font files
```

## Deploying to AWS

### First-Time Setup

1. **Initialize Terraform**
```bash
cd terraform
terraform init
```

2. **Review Configuration**
```bash
# Create terraform.tfvars (optional)
cat > terraform.tfvars <<EOF
aws_region = "us-east-1"
stage = "Prod"
allow_origins = "https://example.com,https://app.example.com"
root_path = "gen/mosaic"
log_level = "INFO"
EOF
```

3. **Plan Deployment**
```bash
terraform plan
```

4. **Deploy**
```bash
terraform apply
```

### Updating Deployment

```bash
# Build new package
cd ..
python scripts/build.py

# Apply Terraform changes
cd terraform
terraform apply
```

### Deployment Checklist

- [ ] Code tested locally
- [ ] All tests passing
- [ ] Dependencies up to date
- [ ] Environment variables configured
- [ ] CORS origins set correctly (not wildcard in production)
- [ ] Build successful
- [ ] Terraform plan reviewed
- [ ] Post-deployment smoke test

## Configuration

### Environment Variables

#### Required for Production
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins
  - Example: `https://app.example.com,https://www.example.com`
  - **DO NOT** use `*` in production

#### Optional
- `ROOT_PATH`: API path prefix (default: `gen/mosaic`)
- `LOG_LEVEL`: Logging verbosity (default: `INFO`)
  - Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- `MAX_IMAGE_SIZE`: Maximum upload size in bytes (default: `10485760` = 10MB)
- `MAX_IMAGE_DIMENSION`: Maximum image dimensions (default: `10000`)

### Terraform Variables

```hcl
# terraform/terraform.tfvars
aws_region = "us-east-1"
stage = "Prod"
allow_origins = "https://your-domain.com"
root_path = "gen/mosaic"
log_level = "INFO"
```

### Lambda Configuration
- **Timeout**: 60 seconds
- **Memory**: 1024 MB
- **Concurrent Executions**: Limited to 10 (prevent cost overruns)
- **Runtime**: Python 3.11
- **Tracing**: X-Ray enabled

## Monitoring

### CloudWatch Alarms

Three alarms are automatically created:

1. **Error Alarm**: Triggers when >5 errors in 1 minute
2. **Duration Alarm**: Triggers when average duration >50 seconds (83% of timeout)
3. **Throttle Alarm**: Triggers when >5 throttles in 1 minute

### Accessing Logs

```bash
# View recent logs
aws logs tail /aws/lambda/TxtMosaicFunction --follow

# Filter by error
aws logs filter-pattern /aws/lambda/TxtMosaicFunction --filter-pattern "ERROR"

# Export logs
aws logs get-log-events \
  --log-group-name /aws/lambda/TxtMosaicFunction \
  --log-stream-name <stream-name>
```

### CloudWatch Insights Queries

```sql
# Find slow requests
fields @timestamp, request_id, duration_ms
| filter event = "mosaic_generated"
| sort duration_ms desc
| limit 20

# Error analysis
fields @timestamp, request_id, error
| filter event = "mosaic_generation_failed"
| stats count() by error

# Request volume
fields @timestamp
| filter event = "mosaic_request_received"
| stats count() by bin(5m)
```

### X-Ray Tracing

View detailed request traces in AWS X-Ray console:
- Service map shows Lambda → downstream services
- Trace details show execution timeline
- Filter by status code, latency, etc.

## Troubleshooting

### Common Issues

#### 1. Lambda Timeout
**Symptom**: 502 errors, timeout in logs

**Solutions**:
- Reduce `target_width` parameter
- Check image size (should be <10MB)
- Verify adequate memory (1024MB)
- Check CloudWatch duration metrics

#### 2. Out of Memory
**Symptom**: Lambda exits with memory error

**Solutions**:
- Reduce image dimensions
- Lower `target_width`
- Increase Lambda memory in Terraform
- Check estimated memory in logs

#### 3. CORS Errors
**Symptom**: Browser console shows CORS error

**Solutions**:
- Verify `ALLOWED_ORIGINS` includes your domain
- Check protocol (http vs https)
- Ensure no wildcard with specific origins
- Test with `curl` to isolate browser issues

#### 4. 413 File Too Large
**Symptom**: Upload rejected with 413 status

**Solutions**:
- Compress image before upload
- Reduce image dimensions
- Check file size (<10MB)
- Verify API Gateway limits

#### 5. Invalid Image Error
**Symptom**: 400 error, "Invalid or malicious image"

**Solutions**:
- Verify file is valid image format
- Try different image format (PNG, JPEG)
- Check image isn't corrupted
- Ensure dimensions >0

### Debugging Steps

1. **Check Health Endpoint**
```bash
curl https://your-api-gateway-url/health
```

2. **Check Logs**
```bash
aws logs tail /aws/lambda/TxtMosaicFunction --follow
```

3. **Test with Minimal Request**
```bash
curl -X POST https://your-api/gen/mosaic/ \
  -F "text=Test" \
  -F "width=200" \
  -F "file=@small-test.png" \
  -v
```

4. **Check CloudWatch Metrics**
- Navigate to AWS Console → Lambda → TxtMosaicFunction
- View "Monitoring" tab
- Check Invocations, Errors, Duration, Throttles

5. **Verify Configuration**
```bash
cd terraform
terraform show | grep environment -A 20
```

### Performance Optimization

#### If Processing is Slow:
- Increase Lambda memory (1536MB or 2048MB)
- Reduce image dimensions before upload
- Use smaller `target_width` values
- Consider caching for repeated requests

#### If Costs are High:
- Reduce concurrent execution limit
- Implement API Gateway caching
- Add request throttling/quotas
- Optimize image sizes

## Rollback Procedure

### Terraform Rollback
```bash
cd terraform

# List workspace states
terraform state list

# Restore previous state
terraform apply -auto-approve

# Or use specific version
git checkout <previous-commit>
terraform apply
```

### Manual Rollback
1. Navigate to AWS Lambda Console
2. Select TxtMosaicFunction
3. Click "Versions" tab
4. Find previous version
5. Update alias to point to previous version

## Security Checklist

- [ ] CORS origins restricted (not `*`)
- [ ] API Gateway has throttling enabled
- [ ] Lambda has execution limits
- [ ] CloudWatch alarms configured
- [ ] X-Ray tracing enabled
- [ ] Logs retention set (14 days)
- [ ] IAM roles follow least privilege
- [ ] Environment variables don't contain secrets
- [ ] API key/authentication in place (if required)

## Support

For issues:
1. Check CloudWatch logs
2. Review CloudWatch alarms
3. Test with minimal inputs
4. Verify configuration
5. Check AWS service health

Contact: [Your team contact info]
