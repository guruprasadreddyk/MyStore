resource "aws_apigatewayv2_api" "api" {
  name          = var.api_name
  protocol_type = "HTTP"

  cors_configuration {
    allow_headers  = ["Content-Type", "Authorization"]
    allow_methods  = ["OPTIONS", "GET", "POST", "PUT", "DELETE"]
    allow_origins  = ["*"]
    expose_headers = ["*"]
    max_age        = 3600
  }
}

# API Gateway throttling to handle higher request rates
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = "$default"
  auto_deploy = true

  # Throttling configuration
  default_route_settings {
    throttling_burst_limit = 100  # Burst requests per second
    throttling_rate_limit  = 50   # Steady-state requests per second
  }
}

resource "aws_apigatewayv2_integration" "integration" {
  for_each = {
    product = aws_lambda_function.function["product"].invoke_arn
    cart    = aws_lambda_function.function["cart"].invoke_arn
    order   = aws_lambda_function.function["order"].invoke_arn
    payment = aws_lambda_function.function["payment"].invoke_arn
    search  = aws_lambda_function.function["search"].invoke_arn
  }

  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = each.value
  payload_format_version = "2.0"
}

locals {
  routes = [
    { name = "products",     route_key = "GET /products",             integration = "product" },
    { name = "product_by_id",route_key = "GET /products/{id}",       integration = "product" },
    { name = "search",       route_key = "GET /search",              integration = "search" },
    { name = "cart_get",     route_key = "GET /cart",                integration = "cart" },
    { name = "cart_add",     route_key = "POST /cart/add",          integration = "cart" },
    { name = "cart_remove",  route_key = "DELETE /cart/remove/{id}",integration = "cart" },
    { name = "cart_clear",   route_key = "DELETE /cart",           integration = "cart" },
    { name = "order_get_all",route_key = "GET /order",              integration = "order" },
    { name = "order_post",   route_key = "POST /order",            integration = "order" },
    { name = "order_get",    route_key = "GET /order/{id}",        integration = "order" },
    { name = "order_put",    route_key = "PUT /order/{id}",        integration = "order" },
    { name = "payment",      route_key = "POST /payment",          integration = "payment" }
  ]
}

resource "aws_apigatewayv2_route" "route" {
  for_each = { for route in local.routes : route.name => route }

  api_id    = aws_apigatewayv2_api.api.id
  route_key = each.value.route_key
  target    = "integrations/${aws_apigatewayv2_integration.integration[each.value.integration].id}"
}

resource "aws_lambda_permission" "allow_api" {
  for_each = {
    product = aws_lambda_function.function["product"].function_name
    cart    = aws_lambda_function.function["cart"].function_name
    order   = aws_lambda_function.function["order"].function_name
    payment = aws_lambda_function.function["payment"].function_name
    search  = aws_lambda_function.function["search"].function_name
  }

  statement_id  = "AllowExecution-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = each.value
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}