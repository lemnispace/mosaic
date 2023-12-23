resource "aws_apigatewayv2_integration" "lemnispace_services_integration" {
  api_id             = var.api_id
  description        = "Lambda integration for Mosaic Service API"
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
  integration_uri    = var.lambda_invoke_arn
}

resource "aws_apigatewayv2_route" "lemnispace_services_route" {
  api_id    = var.api_id
  route_key = "ANY /${var.lambda_endpoint}/{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lemnispace_services_integration.id}"
}
