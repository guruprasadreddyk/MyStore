locals {
  lambda_definitions = {
    product = {
      handler  = "product_service.lambda_handler"
      filename = "${path.module}/../product_service_guru.zip"
    }
    cart = {
      handler  = "cart_service.lambda_handler"
      filename = "${path.module}/../cart_service_guru.zip"
    }
    order = {
      handler  = "order_service.lambda_handler"
      filename = "${path.module}/../order_service_guru.zip"
    }
    payment = {
      handler  = "payment_service.lambda_handler"
      filename = "${path.module}/../payment_service_guru.zip"
    }
    search = {
      handler  = "search_service.lambda_handler"
      filename = "${path.module}/../search_service_guru.zip"
    }
    processor = {
      handler  = "order_processor.lambda_handler"
      filename = "${path.module}/../order_processor_guru.zip"
    }
  }
}

resource "aws_lambda_function" "function" {
  for_each = local.lambda_definitions

  function_name = "${each.key}_service_guru"
  handler       = each.value.handler
  runtime       = "python3.12"
  role          = aws_iam_role.lambda_role.arn
  filename      = each.value.filename
  source_code_hash = filebase64sha256(each.value.filename)
}

# SQS Event Source Mapping for order processor
resource "aws_lambda_event_source_mapping" "order_processor_sqs" {
  event_source_arn = aws_sqs_queue.order_processing.arn
  function_name    = aws_lambda_function.function["processor"].arn
  batch_size       = 1  # Process one message at a time
}
