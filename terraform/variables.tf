variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "stage" {
  description = "Deployment stage (e.g., Dev, Staging, Prod)"
  type        = string
  default     = "Dev"
}

variable "allow_origins" {
  description = "Comma-separated list of allowed origins for CORS (use specific origins in production, not '*')"
  type        = string
  default     = "*"

  validation {
    condition     = length(var.allow_origins) > 0
    error_message = "ALLOWED_ORIGINS cannot be empty"
  }
}

variable "root_path" {
  description = "Root path for the API Gateway endpoint"
  type        = string
  default     = "gen/mosaic"
}

variable "log_level" {
  description = "Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
  type        = string
  default     = "INFO"

  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.log_level)
    error_message = "log_level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL"
  }
}
