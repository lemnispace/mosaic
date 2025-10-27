terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket         = "lemnispace-terraform-state"
    key            = "mosaic-service/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region = var.aws_region
}

data "terraform_remote_state" "lemnispace_services" {
  backend = "s3"
  config = {
    bucket         = "lemnispace-terraform-state"
    key            = "infra/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-lock"
  }
}


module "mosaic_route" {
  source            = "./modules/routes"
  lambda_endpoint   = var.root_path
  lambda_invoke_arn = aws_lambda_function.TxtMosaicFunction.invoke_arn
  api_id            = data.terraform_remote_state.lemnispace_services.outputs.api_id
}

### S3 Bucket for Lambda Function ###
data "archive_file" "TxtMosaicFunction" {
  type        = "zip"
  source_dir  = "${path.module}/../.aws-sam/build/MosaicFunction"
  output_path = "${path.module}/../.aws-sam/TxtMosaicFunction.zip"
}

resource "aws_s3_object" "mosaic_service" {
  bucket = data.terraform_remote_state.lemnispace_services.outputs.services_s3_bucket_id
  key    = "TxtMosaicFunction.zip"

  source = data.archive_file.TxtMosaicFunction.output_path
  etag   = filemd5(data.archive_file.TxtMosaicFunction.output_path)
}

### CloudWatch Logs ###
resource "aws_cloudwatch_log_group" "mosaic_logs" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = 14

  tags = {
    Environment = var.stage
    Service     = "mosaic"
  }
}

### Lambda Function ###
resource "aws_lambda_function" "TxtMosaicFunction" {
  filename         = data.archive_file.TxtMosaicFunction.output_path
  function_name    = local.function_name
  role             = data.terraform_remote_state.lemnispace_services.outputs.execute_lambda_role_arn
  handler          = "main.handler"
  runtime          = "python3.11"
  source_code_hash = data.archive_file.TxtMosaicFunction.output_base64sha256

  # Increased for production-grade image processing
  timeout     = 60
  memory_size = 1024

  # Limit concurrent executions to prevent cost overruns
  reserved_concurrent_executions = 10

  # Enable X-Ray tracing for observability
  tracing_config {
    mode = "Active"
  }

  environment {
    variables = {
      ALLOWED_ORIGINS      = var.allow_origins
      ROOT_PATH            = var.root_path
      LOG_LEVEL            = var.log_level
      MAX_IMAGE_SIZE       = "10485760" # 10MB
      MAX_IMAGE_DIMENSION  = "10000"
    }
  }

  # Ensure log group is created first
  depends_on = [aws_cloudwatch_log_group.mosaic_logs]

  tags = {
    Environment = var.stage
    Service     = "mosaic"
  }
}

resource "aws_lambda_permission" "mosaic_service" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.TxtMosaicFunction.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${data.terraform_remote_state.lemnispace_services.outputs.api_execution_arn}/*/*"
}

### CloudWatch Alarms ###
resource "aws_cloudwatch_metric_alarm" "mosaic_errors" {
  alarm_name          = "${local.function_name}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "Alert when mosaic function has more than 5 errors in 1 minute"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.TxtMosaicFunction.function_name
  }

  tags = {
    Environment = var.stage
    Service     = "mosaic"
  }
}

resource "aws_cloudwatch_metric_alarm" "mosaic_duration" {
  alarm_name          = "${local.function_name}-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Average"
  threshold           = "50000" # 50 seconds (83% of 60s timeout)
  alarm_description   = "Alert when mosaic function duration approaches timeout"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.TxtMosaicFunction.function_name
  }

  tags = {
    Environment = var.stage
    Service     = "mosaic"
  }
}

resource "aws_cloudwatch_metric_alarm" "mosaic_throttles" {
  alarm_name          = "${local.function_name}-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "Alert when mosaic function is being throttled"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.TxtMosaicFunction.function_name
  }

  tags = {
    Environment = var.stage
    Service     = "mosaic"
  }
}

### Local Variables ###
locals {
  function_name = "TxtMosaicFunction"
}