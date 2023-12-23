output "TxtMosaicFunction_name" {
  description = "The name of the lambda function"
  value       = aws_lambda_function.TxtMosaicFunction.function_name
}

output "TxtMosaicFunction_arn" {
  description = "The ARN of the lambda function"
  value       = aws_lambda_function.TxtMosaicFunction.arn
}

output "mosaic_route_id" {
  description = "The ID of the mosaic service route"
  value       = module.mosaic_route.route_id
}

output "mosaic_route_uri" {
  description = "The URI of the mosaic service route"
  value       = module.mosaic_route.route_uri
}

output "mosaic_route_hash" {
  description = "The hash of the mosaic service route. Used for deployments to trigger when the route changes"
  value       = module.mosaic_route.route_hash
}
