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

resource "aws_apigatewayv2_authorizer" "auth0" {
  api_id           = aws_apigatewayv2_api.api.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "auth0-authorizer"

  jwt_configuration {
    audience = ["https://api.mystore.com"]
    issuer   = "https://dev-sjgq3v6pvbgxs6mb.us.auth0.com/"
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
    wishlist = aws_lambda_function.function["wishlist"].invoke_arn
  }

  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = each.value
  payload_format_version = "2.0"
}

locals {
  routes = [
    { name = "products",     route_key = "GET /products",             integration = "product", protected = false },
    { name = "product_by_id",route_key = "GET /products/{id}",       integration = "product", protected = false },
    { name = "search",       route_key = "GET /search",              integration = "search", protected = false },
    { name = "recommendations",route_key = "GET /recommendations",    integration = "product", protected = false },
    { name = "cart_get",     route_key = "GET /cart",                integration = "cart", protected = true },
    { name = "cart_add",     route_key = "POST /cart/add",          integration = "cart", protected = true },
    { name = "cart_remove",  route_key = "DELETE /cart/remove/{id}",integration = "cart", protected = true },
    { name = "cart_clear",   route_key = "DELETE /cart",           integration = "cart", protected = true },
    { name = "order_get_all",route_key = "GET /order",              integration = "order", protected = true },
    { name = "order_post",   route_key = "POST /order",            integration = "order", protected = true },
    { name = "order_get",    route_key = "GET /order/{id}",        integration = "order", protected = true },
    { name = "order_put",    route_key = "PUT /order/{id}",        integration = "order", protected = true },
    { name = "payment",      route_key = "POST /payment",          integration = "payment", protected = true },
    { name = "wishlist_get", route_key = "GET /wishlist",          integration = "wishlist", protected = true },
    { name = "wishlist_add", route_key = "POST /wishlist/add",     integration = "wishlist", protected = true },
    { name = "wishlist_remove",route_key = "DELETE /wishlist/remove/{id}",integration = "wishlist", protected = true }
  ]
}

resource "aws_apigatewayv2_route" "route" {
  for_each = { for route in local.routes : route.name => route }

  api_id    = aws_apigatewayv2_api.api.id
  route_key = each.value.route_key
  target    = "integrations/${aws_apigatewayv2_integration.integration[each.value.integration].id}"

  authorization_type = each.value.protected ? "JWT" : "NONE"
  authorizer_id      = each.value.protected ? aws_apigatewayv2_authorizer.auth0.id : null
}

resource "aws_lambda_permission" "allow_api" {
  for_each = {
    product = aws_lambda_function.function["product"].function_name
    cart    = aws_lambda_function.function["cart"].function_name
    order   = aws_lambda_function.function["order"].function_name
    payment = aws_lambda_function.function["payment"].function_name
    search  = aws_lambda_function.function["search"].function_name
    wishlist = aws_lambda_function.function["wishlist"].function_name
  }

  statement_id  = "AllowExecution-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = each.value
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}