output "TxtMosaicFunction_name" {
  description = "The name of the lambda function"
  value = aws_lambda_function.TxtMosaicFunction.function_name
}

output "TxtMosaicFunction_arn" {
  description = "The ARN of the lambda function"
  value = aws_lambda_function.TxtMosaicFunction.arn
}