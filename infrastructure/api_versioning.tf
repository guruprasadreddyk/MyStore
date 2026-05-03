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
    { name = "v1_products",         route_key = "GET /v1/products",                    integration = "catalog",  protected = false },
    { name = "v1_product_by_id",    route_key = "GET /v1/products/{id}",              integration = "catalog",  protected = false },
    { name = "v1_search",           route_key = "GET /v1/search",                     integration = "catalog",  protected = false },
    { name = "v1_recommendations",  route_key = "GET /v1/recommendations",            integration = "catalog",  protected = false },
    { name = "v1_cart_get",         route_key = "GET /v1/cart",                       integration = "cart",     protected = true },
    { name = "v1_cart_add",         route_key = "POST /v1/cart/add",                  integration = "cart",     protected = true },
    { name = "v1_cart_remove",      route_key = "DELETE /v1/cart/remove/{id}",        integration = "cart",     protected = true },
    { name = "v1_cart_clear",       route_key = "DELETE /v1/cart",                    integration = "cart",     protected = true },
    { name = "v1_wishlist_get",     route_key = "GET /v1/wishlist",                   integration = "cart",     protected = true },
    { name = "v1_wishlist_add",     route_key = "POST /v1/wishlist/add",              integration = "cart",     protected = true },
    { name = "v1_wishlist_remove",  route_key = "DELETE /v1/wishlist/remove/{id}",    integration = "cart",     protected = true },
    { name = "v1_addresses_get",    route_key = "GET /v1/addresses",                  integration = "cart",     protected = true },
    { name = "v1_addresses_post",   route_key = "POST /v1/addresses",                 integration = "cart",     protected = true },
    { name = "v1_addresses_put",    route_key = "PUT /v1/addresses/{id}",             integration = "cart",     protected = true },
    { name = "v1_addresses_del",    route_key = "DELETE /v1/addresses/{id}",          integration = "cart",     protected = true },
    { name = "v1_profile_get",      route_key = "GET /v1/profile/me",                 integration = "cart",     protected = true },
    { name = "v1_profile_put",      route_key = "PUT /v1/profile/me",                 integration = "cart",     protected = true },
    { name = "v1_profile_verify",   route_key = "POST /v1/profile/verify-email",      integration = "cart",     protected = true },
    { name = "v1_order_get_all",    route_key = "GET /v1/order",                      integration = "order",    protected = true },
    { name = "v1_order_post",       route_key = "POST /v1/order",                     integration = "order",    protected = true },
    { name = "v1_order_get",        route_key = "GET /v1/order/{id}",                 integration = "order",    protected = true },
    { name = "v1_order_put",        route_key = "PUT /v1/order/{id}",                 integration = "order",    protected = true },
    { name = "v1_order_cancel",     route_key = "DELETE /v1/order/{id}",              integration = "order",    protected = true },
    { name = "v1_payment",          route_key = "POST /v1/payment",                   integration = "payment",  protected = true },
    { name = "v1_admin_dashboard",  route_key = "GET /v1/admin/dashboard",            integration = "admin",    protected = true },
    { name = "v1_admin_prod_get",   route_key = "GET /v1/admin/products",             integration = "admin",    protected = true },
    { name = "v1_admin_prod_post",  route_key = "POST /v1/admin/products",            integration = "admin",    protected = true },
    { name = "v1_admin_prod_put",   route_key = "PUT /v1/admin/products/{id}",        integration = "admin",    protected = true },
    { name = "v1_admin_prod_del",   route_key = "DELETE /v1/admin/products/{id}",     integration = "admin",    protected = true },
    { name = "v1_admin_orders_get", route_key = "GET /v1/admin/orders",               integration = "admin",    protected = true },
    { name = "v1_admin_orders_put", route_key = "PUT /v1/admin/orders/{id}",          integration = "admin",    protected = true },
  ]
}

resource "aws_apigatewayv2_route" "v1_route" {
  for_each = { for route in local.v1_routes : route.name => route }

  api_id    = aws_apigatewayv2_api.api.id
  route_key = each.value.route_key
  target    = "integrations/${aws_apigatewayv2_integration.integration[each.value.integration].id}"

  authorization_type = each.value.protected ? "JWT" : "NONE"
  authorizer_id      = each.value.protected ? aws_apigatewayv2_authorizer.auth0.id : null
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