# SQS Queue for order processing
resource "aws_sqs_queue" "order_processing" {
  name = var.sqs_queue_name

  # Enable dead letter queue (optional)
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.order_processing_dlq.arn
    maxReceiveCount     = 5
  })

  # Visibility timeout (time message is invisible after being received)
  visibility_timeout_seconds = 300

  # Message retention period (4 days)
  message_retention_seconds = 345600
}

# Dead Letter Queue for failed messages
resource "aws_sqs_queue" "order_processing_dlq" {
  name = "${var.sqs_queue_name}-dlq"
}

# SNS Topic for order notifications
resource "aws_sns_topic" "order_notifications" {
  name = var.sns_topic_name
}

# Optional: SNS Topic Policy (allow publishing from Lambda)
resource "aws_sns_topic_policy" "order_notifications_policy" {
  arn = aws_sns_topic.order_notifications.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        AWS = aws_iam_role.lambda_role.arn
      }
      Action   = "sns:Publish"
      Resource = aws_sns_topic.order_notifications.arn
    }]
  })
}

# SNS Subscription: Send notifications to SQS queue
resource "aws_sns_topic_subscription" "order_notifications_to_sqs" {
  topic_arn = aws_sns_topic.order_notifications.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.order_processing.arn
}

# SNS Subscription: Send email notifications (replace with your email)
resource "aws_sns_topic_subscription" "order_notifications_email" {
  topic_arn = aws_sns_topic.order_notifications.arn
  protocol  = "email"
  endpoint  = "guruprasad.reddy@idp.com"  # Replace with actual email
}

# SQS Queue Policy: Allow SNS to send messages
resource "aws_sqs_queue_policy" "order_processing_policy" {
  queue_url = aws_sqs_queue.order_processing.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "sns.amazonaws.com"
      }
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.order_processing.arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = aws_sns_topic.order_notifications.arn
        }
      }
    }]
  })
}