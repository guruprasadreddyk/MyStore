resource "random_string" "suffix" {
  length  = 8
  lower   = true
  upper   = false
  numeric = true
  special = false
}

# -------------------------
# S3 BUCKET (MISSING BEFORE)
# -------------------------
resource "aws_s3_bucket" "frontend" {
  bucket = "${var.frontend_bucket_prefix}-${random_string.suffix.result}"
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# -------------------------
# CLOUDFRONT OAI (MISSING BEFORE)
# -------------------------
resource "aws_cloudfront_origin_access_identity" "frontend" {
  comment = "OAI for ecommerce frontend"
}

# -------------------------
# S3 POLICY
# -------------------------
resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontAccess"
        Effect = "Allow"

        Principal = {
          CanonicalUser = aws_cloudfront_origin_access_identity.frontend.s3_canonical_user_id
        }

        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.frontend.arn}/*"
      }
    ]
  })
}

# -------------------------
# CLOUDFRONT DISTRIBUTION
# -------------------------
resource "aws_cloudfront_distribution" "frontend" {
  enabled         = true
  is_ipv6_enabled = true

  default_root_object = "index.html"

  origin {
    domain_name = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id   = "s3-frontend"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.frontend.cloudfront_access_identity_path
    }
  }

  origin {
    domain_name = replace(aws_apigatewayv2_api.api.api_endpoint, "https://", "")
    origin_id   = "api-backend"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id = "s3-frontend"

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD"]

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }

    viewer_protocol_policy = "redirect-to-https"
  }

  ordered_cache_behavior {
    path_pattern     = "/products*"
    target_origin_id = "api-backend"

    allowed_methods = ["HEAD", "GET", "OPTIONS", "DELETE", "POST", "PUT", "PATCH"]
    cached_methods  = ["GET", "HEAD"]

    viewer_protocol_policy = "redirect-to-https"

    cache_policy_id = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
  }

  ordered_cache_behavior {
    path_pattern     = "/search*"
    target_origin_id = "api-backend"

    allowed_methods = ["HEAD", "GET", "OPTIONS", "DELETE", "POST", "PUT", "PATCH"]
    cached_methods  = ["GET", "HEAD"]

    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = true
      cookies { forward = "none" }
    }
  }

  ordered_cache_behavior {
    path_pattern     = "/cart*"
    target_origin_id = "api-backend"

    allowed_methods = ["HEAD", "GET", "OPTIONS", "DELETE", "POST", "PUT", "PATCH"]
    cached_methods  = ["GET", "HEAD"]

    viewer_protocol_policy = "redirect-to-https"

    cache_policy_id = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
  }

  ordered_cache_behavior {
    path_pattern     = "/order*"
    target_origin_id = "api-backend"

    allowed_methods = ["HEAD", "GET", "OPTIONS", "DELETE", "POST", "PUT", "PATCH"]
    cached_methods  = ["GET", "HEAD"]

    viewer_protocol_policy = "redirect-to-https"

    cache_policy_id = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
  }

  ordered_cache_behavior {
    path_pattern     = "/payment*"
    target_origin_id = "api-backend"

    allowed_methods = ["HEAD", "GET", "OPTIONS", "DELETE", "POST", "PUT", "PATCH"]
    cached_methods  = ["GET", "HEAD"]

    viewer_protocol_policy = "redirect-to-https"

    cache_policy_id = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}