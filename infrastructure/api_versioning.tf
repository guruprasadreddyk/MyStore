# API Versioning with Stages
resource "aws_apigatewayv2_stage" "v1" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = "v1"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 100
    throttling_rate_limit  = 50
  }
}


# Versioned routes with v1 prefix
locals {
  v1_routes = [
    { name = "v1_products",         route_key = "GET /v1/products",             integration = "product" },
    { name = "v1_product_by_id",    route_key = "GET /v1/products/{id}",       integration = "product" },
    { name = "v1_search",           route_key = "GET /v1/search",              integration = "search" },
    { name = "v1_cart_get",         route_key = "GET /v1/cart",                integration = "cart" },
    { name = "v1_cart_add",         route_key = "POST /v1/cart/add",          integration = "cart" },
    { name = "v1_cart_remove",      route_key = "DELETE /v1/cart/remove/{id}",integration = "cart" },
    { name = "v1_cart_clear",       route_key = "DELETE /v1/cart",           integration = "cart" },
    { name = "v1_order_get_all",    route_key = "GET /v1/order",              integration = "order" },
    { name = "v1_order_post",       route_key = "POST /v1/order",            integration = "order" },
    { name = "v1_order_get",        route_key = "GET /v1/order/{id}",        integration = "order" },
    { name = "v1_order_put",        route_key = "PUT /v1/order/{id}",        integration = "order" },
    { name = "v1_payment",          route_key = "POST /v1/payment",          integration = "payment" }
  ]
}

resource "aws_apigatewayv2_route" "v1_route" {
  for_each = { for route in local.v1_routes : route.name => route }

  api_id    = aws_apigatewayv2_api.api.id
  route_key = each.value.route_key
  target    = "integrations/${aws_apigatewayv2_integration.integration[each.value.integration].id}"
}

# Custom Domain (Optional - requires ACM certificate)
# Uncomment and configure for production custom domain
/*
resource "aws_acm_certificate" "api" {
  domain_name       = "api.yourdomain.com"
  validation_method = "DNS"

  tags = {
    Name = "api-certificate"
  }
}

resource "aws_apigatewayv2_domain_name" "api" {
  domain_name = "api.yourdomain.com"

  domain_name_configuration {
    certificate_arn = aws_acm_certificate.api.arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
}

resource "aws_route53_record" "api" {
  zone_id = var.route53_zone_id
  name    = "api.yourdomain.com"
  type    = "A"

  alias {
    name                   = aws_apigatewayv2_domain_name.api.domain_name_configuration[0].target_domain_name
    zone_id               = aws_apigatewayv2_domain_name.api.domain_name_configuration[0].hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_apigatewayv2_api_mapping" "api" {
  api_id      = aws_apigatewayv2_api.api.id
  domain_name = aws_apigatewayv2_domain_name.api.id
  stage       = aws_apigatewayv2_stage.v1.id
}
*/