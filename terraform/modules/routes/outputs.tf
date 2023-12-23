output "route_id" {
  value = aws_apigatewayv2_route.lemnispace_services_route.id
}

output "route_uri" {
  value = aws_apigatewayv2_route.lemnispace_services_route.target
}

output "route_hash" {
  value = sha1(jsonencode(aws_apigatewayv2_route.lemnispace_services_route))
}