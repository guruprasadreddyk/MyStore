output "api_url" {
  value = aws_apigatewayv2_api.api.api_endpoint
}

output "cloudfront_url" {
  value = aws_cloudfront_distribution.frontend.domain_name
}

output "s3_bucket_name" {
  value = aws_s3_bucket.frontend.bucket
}

output "sqs_queue_url" {
  value = aws_sqs_queue.order_processing.url
}

output "sns_topic_arn" {
  value = aws_sns_topic.order_notifications.arn
}