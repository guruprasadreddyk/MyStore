resource "aws_apigatewayv2_api" "api" {
  name          = var.api_name
  protocol_type = "HTTP"

  cors_configuration {
    allow_headers  = ["Content-Type", "Authorization"]
    allow_methods  = ["OPTIONS", "GET", "POST", "PUT", "DELETE"]
    allow_origins  = [
      "https://${var.frontend_domain}",
      "http://localhost:3000"
    ]
    expose_headers = ["Content-Type"]
    max_age        = 3600
  }
}

resource "aws_apigatewayv2_authorizer" "auth0" {
  api_id           = aws_apigatewayv2_api.api.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "auth0-authorizer"

  jwt_configuration {
    audience = [var.auth0_audience]
    issuer   = "https://${var.auth0_domain}/"
  }
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_access_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      method         = "$context.httpMethod"
      path           = "$context.path"
      status         = "$context.status"
      latency        = "$context.responseLatency"
      user           = "$context.authorizer.claims.sub"
      requestTime    = "$context.requestTime"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      errorMessage   = "$context.error.message"
    })
  }

  # Global default — applies to every route not listed below
  default_route_settings {
    throttling_burst_limit = 100
    throttling_rate_limit  = 50
  }

  # Payment — tightest limit (expensive, fraud-sensitive)
  route_settings {
    route_key              = "POST /payment"
    throttling_burst_limit = 10
    throttling_rate_limit  = 5
  }

  route_settings {
    route_key              = "POST /payment/create-order"
    throttling_burst_limit = 10
    throttling_rate_limit  = 5
  }

  # Order creation — moderate limit
  route_settings {
    route_key              = "POST /order"
    throttling_burst_limit = 20
    throttling_rate_limit  = 10
  }

  # Admin — low limit, internal use only
  route_settings {
    route_key              = "GET /admin/dashboard"
    throttling_burst_limit = 10
    throttling_rate_limit  = 5
  }

  # Public product browsing — higher limit, read-only
  route_settings {
    route_key              = "GET /products"
    throttling_burst_limit = 200
    throttling_rate_limit  = 100
  }

  route_settings {
    route_key              = "GET /search"
    throttling_burst_limit = 100
    throttling_rate_limit  = 50
  }
}

# ── Lambda integrations (one per Lambda function) ─────────────────────────────
resource "aws_apigatewayv2_integration" "integration" {
  for_each = {
    catalog = aws_lambda_function.function["catalog"].invoke_arn
    user    = aws_lambda_function.function["user"].invoke_arn
    order   = aws_lambda_function.function["order"].invoke_arn
    payment = aws_lambda_function.function["payment"].invoke_arn
    admin   = aws_lambda_function.function["admin"].invoke_arn
  }

  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = each.value
  payload_format_version = "2.0"
}

# ── Routes ────────────────────────────────────────────────────────────────────
locals {
  routes = [
    # Catalog (public)
    { name = "products",        route_key = "GET /products",                    integration = "catalog",  protected = false },
    { name = "product_by_id",   route_key = "GET /products/{id}",              integration = "catalog",  protected = false },
    { name = "search",          route_key = "GET /search",                     integration = "catalog",  protected = false },
    { name = "recommendations", route_key = "GET /recommendations",            integration = "catalog",  protected = false },
    { name = "health",          route_key = "GET /health",                     integration = "catalog",  protected = false },
    
    # Product Variants (public)
    { name = "variants_get",    route_key = "GET /products/{id}/variants",     integration = "catalog",  protected = false },
    { name = "variant_get",     route_key = "GET /products/{id}/variants/{variant_id}", integration = "catalog", protected = false },
    
    # Product Reviews (public read, authenticated write)
    { name = "reviews_get",     route_key = "GET /products/{id}/reviews",      integration = "catalog",  protected = false },
    { name = "reviews_post",    route_key = "POST /products/{id}/reviews",     integration = "catalog",  protected = true },
    { name = "review_helpful",  route_key = "PUT /reviews/{id}/helpful",       integration = "catalog",  protected = false },
    { name = "review_delete",   route_key = "DELETE /reviews/{id}",            integration = "catalog",  protected = true },

    # Cart + Wishlist (authenticated)
    { name = "cart_get",        route_key = "GET /cart",                       integration = "user",     protected = true },
    { name = "cart_add",        route_key = "POST /cart/add",                  integration = "user",     protected = true },
    { name = "cart_remove",     route_key = "DELETE /cart/remove/{id}",        integration = "user",     protected = true },
    { name = "cart_clear",      route_key = "DELETE /cart",                    integration = "user",     protected = true },
    { name = "wishlist_get",    route_key = "GET /wishlist",                   integration = "user",     protected = true },
    { name = "wishlist_add",    route_key = "POST /wishlist/add",              integration = "user",     protected = true },
    { name = "wishlist_remove", route_key = "DELETE /wishlist/remove/{id}",    integration = "user",     protected = true },

    # Saved Addresses
    { name = "addresses_get",   route_key = "GET /addresses",                  integration = "user",     protected = true },
    { name = "addresses_post",  route_key = "POST /addresses",                 integration = "user",     protected = true },
    { name = "addresses_put",   route_key = "PUT /addresses/{id}",             integration = "user",     protected = true },
    { name = "addresses_del",   route_key = "DELETE /addresses/{id}",          integration = "user",     protected = true },

    # User profile (editable display name, phone, bio — stored in DynamoDB)
    { name = "profile_get",     route_key = "GET /profile/me",                 integration = "user",     protected = true },
    { name = "profile_put",     route_key = "PUT /profile/me",                 integration = "user",     protected = true },
    { name = "profile_verify",  route_key = "POST /profile/verify-email",      integration = "user",     protected = true },

    # Orders (authenticated)
    { name = "order_get_all",   route_key = "GET /order",                      integration = "order",    protected = true },
    { name = "order_post",      route_key = "POST /order",                     integration = "order",    protected = true },
    { name = "order_get",       route_key = "GET /order/{id}",                 integration = "order",    protected = true },
    { name = "order_put",       route_key = "PUT /order/{id}",                 integration = "order",    protected = true },
    { name = "order_cancel",    route_key = "DELETE /order/{id}",              integration = "order",    protected = true },

    # Returns (authenticated)
    { name = "return_post",     route_key = "POST /return",                    integration = "order",    protected = true },
    { name = "return_get",      route_key = "GET /return/{id}",                integration = "order",    protected = true },

    # Payment (authenticated)
    { name = "payment",              route_key = "POST /payment",                   integration = "payment",  protected = true },
    { name = "payment_create_order", route_key = "POST /payment/create-order",      integration = "payment",  protected = true },

    # Admin (authenticated — role checked inside Lambda)
    { name = "admin_dashboard", route_key = "GET /admin/dashboard",            integration = "admin",    protected = true },
    { name = "admin_products_get",  route_key = "GET /admin/products",         integration = "admin",    protected = true },
    { name = "admin_products_post", route_key = "POST /admin/products",        integration = "admin",    protected = true },
    { name = "admin_products_put",  route_key = "PUT /admin/products/{id}",    integration = "admin",    protected = true },
    { name = "admin_products_del",  route_key = "DELETE /admin/products/{id}", integration = "admin",    protected = true },
    { name = "admin_orders_get",    route_key = "GET /admin/orders",           integration = "admin",    protected = true },
    { name = "admin_orders_put",    route_key = "PUT /admin/orders/{id}",      integration = "admin",    protected = true },
    { name = "admin_returns_get",   route_key = "GET /admin/returns",          integration = "admin",    protected = true },
    { name = "admin_returns_approve", route_key = "PUT /admin/returns/{id}/approve", integration = "admin", protected = true },
    { name = "admin_returns_reject",  route_key = "PUT /admin/returns/{id}/reject",  integration = "admin", protected = true },
    { name = "admin_returns_refund",  route_key = "PUT /admin/returns/{id}/refund",  integration = "admin", protected = true },
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

# ── Lambda invoke permissions ─────────────────────────────────────────────────
resource "aws_lambda_permission" "allow_api" {
  for_each = {
    catalog = aws_lambda_function.function["catalog"].function_name
    user    = aws_lambda_function.function["user"].function_name
    order   = aws_lambda_function.function["order"].function_name
    payment = aws_lambda_function.function["payment"].function_name
    admin   = aws_lambda_function.function["admin"].function_name
  }

  statement_id  = "AllowExecution-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = each.value
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}
