locals {
  lambda_definitions = {
    catalog = {
      handler  = "catalog_service.lambda_handler"
      filename = "${path.module}/../catalog_service_guru.zip"
      role_arn = aws_iam_role.catalog_role.arn
    }
    user = {
      handler  = "user_service.lambda_handler"
      filename = "${path.module}/../user_service_guru.zip"
      role_arn = aws_iam_role.user_role.arn
    }
    order = {
      handler  = "order_service.lambda_handler"
      filename = "${path.module}/../order_service_guru.zip"
      role_arn = aws_iam_role.order_role.arn
    }
    payment = {
      handler  = "payment_service.lambda_handler"
      filename = "${path.module}/../payment_service_guru.zip"
      role_arn = aws_iam_role.payment_role.arn
    }
    processor = {
      handler  = "order_processor.lambda_handler"
      filename = "${path.module}/../order_processor_guru.zip"
      role_arn = aws_iam_role.processor_role.arn
    }
    admin = {
      handler  = "admin_service.lambda_handler"
      filename = "${path.module}/../admin_service_guru.zip"
      role_arn = aws_iam_role.admin_role.arn
    }
  }
}

resource "aws_lambda_function" "function" {
  for_each = local.lambda_definitions

  function_name    = "${each.key}_service_guru"
  handler          = each.value.handler
  runtime          = "python3.12"
  role             = each.value.role_arn
  filename         = each.value.filename
  source_code_hash = filebase64sha256(each.value.filename)
  timeout          = 30

  # Common env vars for all functions
  environment {
    variables = merge(
      {
        SQS_QUEUE_NAME      = var.sqs_queue_name
        SNS_TOPIC_NAME      = var.sns_topic_name
        AWS_REGION_NAME     = var.aws_region
        CORS_ALLOWED_ORIGIN = "https://${var.frontend_domain}"
        SMTP_USER           = var.smtp_user
        SMTP_PASSWORD       = var.smtp_password
        SMTP_FROM           = var.smtp_from
      },
      # Auth0 M2M credentials — only injected into user_service
      each.key == "user" ? {
        AUTH0_DOMAIN            = var.auth0_domain
        AUTH0_M2M_CLIENT_ID     = var.auth0_m2m_client_id
        AUTH0_M2M_CLIENT_SECRET = var.auth0_m2m_client_secret
      } :
      # Razorpay credentials — only injected into payment_service
      each.key == "payment" ? {
        RAZORPAY_KEY_ID     = var.razorpay_key_id
        RAZORPAY_KEY_SECRET = var.razorpay_key_secret
      } : {}
    )
  }
}

# SQS Event Source Mapping for order processor
resource "aws_lambda_event_source_mapping" "order_processor_sqs" {
  event_source_arn = aws_sqs_queue.order_processing.arn
  function_name    = aws_lambda_function.function["processor"].arn
  batch_size       = 1
}
