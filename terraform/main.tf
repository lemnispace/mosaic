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

### Lambda Function ###
resource "aws_lambda_function" "TxtMosaicFunction" {
  filename         = data.archive_file.TxtMosaicFunction.output_path
  function_name    = "TxtMosaicFunction"
  role             = data.terraform_remote_state.lemnispace_services.outputs.execute_lambda_role_arn
  handler          = "main.handler"
  runtime          = "python3.11"
  source_code_hash = data.archive_file.TxtMosaicFunction.output_base64sha256
  environment {
    variables = {
      ALLOWED_ORIGINS = var.allow_origins
      ROOT_PATH       = var.root_path
    }
  }
}

resource "aws_lambda_permission" "mosaic_service" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.TxtMosaicFunction.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${data.terraform_remote_state.lemnispace_services.outputs.api_execution_arn}/*/*"
}