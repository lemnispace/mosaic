variable "aws_region" {
  description = "AWS region for all resources."

  type    = string
  default = "us-east-1"
}

variable "stage" {
  description = "Stage for the API Gateway where the lambda function will be deployed to"
  type        = string
  default     = "Dev"
}

variable "allow_origins" {
  description = "Comma-separated list of allowed origins for CORS"
  type        = string
  default     = "*"
}

variable "root_path" {
  description = "Root path for the API Gateway where the lambda function will be deployed to"
  type        = string
  default     = "gen/mosaic"
}
