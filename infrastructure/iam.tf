# ─── Per-function IAM roles with least-privilege policies ─────────────────────
#
# Each Lambda gets its own role with only the permissions it needs.
# This ensures that a compromise of one function cannot access resources
# belonging to other services.

# ─── Catalog Service Role ─────────────────────────────────────────────────────
resource "aws_iam_role" "catalog_role" {
  name = "catalog_service_role_guru"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "catalog_logs" {
  role       = aws_iam_role.catalog_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "catalog_policy" {
  name = "catalog-service-policy"
  role = aws_iam_role.catalog_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadProducts"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem"
        ]
        Resource = [
          aws_dynamodb_table.products_table.arn,
          "${aws_dynamodb_table.products_table.arn}/index/*"
        ]
      },
      {
        Sid    = "UpdateProductRating"
        Effect = "Allow"
        Action = ["dynamodb:UpdateItem"]
        Resource = [aws_dynamodb_table.products_table.arn]
      },
      {
        Sid    = "ReadWriteReviews"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.reviews_table.arn,
          "${aws_dynamodb_table.reviews_table.arn}/index/*"
        ]
      },
      {
        Sid    = "ReadOrdersForVerifiedPurchase"
        Effect = "Allow"
        Action = ["dynamodb:Query"]
        Resource = [
          "${aws_dynamodb_table.orders_table.arn}/index/*"
        ]
      }
    ]
  })
}

# ─── User Service Role ────────────────────────────────────────────────────────
resource "aws_iam_role" "user_role" {
  name = "user_service_role_guru"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "user_logs" {
  role       = aws_iam_role.user_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "user_policy" {
  name = "user-service-policy"
  role = aws_iam_role.user_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadWriteCart"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem"
        ]
        Resource = [aws_dynamodb_table.cart_table.arn]
      },
      {
        Sid    = "ReadWriteWishlist"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem"
        ]
        Resource = [aws_dynamodb_table.wishlist_table.arn]
      },
      {
        Sid    = "ReadWriteUserData"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = [aws_dynamodb_table.user_data_table.arn]
      },
      {
        Sid    = "ReadProducts"
        Effect = "Allow"
        Action = ["dynamodb:GetItem"]
        Resource = [aws_dynamodb_table.products_table.arn]
      }
    ]
  })
}

# ─── Order Service Role ───────────────────────────────────────────────────────
resource "aws_iam_role" "order_role" {
  name = "order_service_role_guru"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "order_logs" {
  role       = aws_iam_role.order_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "order_policy" {
  name = "order-service-policy"
  role = aws_iam_role.order_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadWriteOrders"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query"
        ]
        Resource = [
          aws_dynamodb_table.orders_table.arn,
          "${aws_dynamodb_table.orders_table.arn}/index/*"
        ]
      },
      {
        Sid    = "ReadWriteCart"
        Effect = "Allow"
        Action = ["dynamodb:GetItem", "dynamodb:PutItem"]
        Resource = [aws_dynamodb_table.cart_table.arn]
      },
      {
        Sid    = "ReadWriteInventory"
        Effect = "Allow"
        Action = ["dynamodb:GetItem", "dynamodb:UpdateItem"]
        Resource = [aws_dynamodb_table.products_table.arn]
      },
      {
        Sid    = "ReadWriteReturns"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query"
        ]
        Resource = [
          aws_dynamodb_table.returns_table.arn,
          "${aws_dynamodb_table.returns_table.arn}/index/*"
        ]
      },
      {
        Sid    = "SNSPublish"
        Effect = "Allow"
        Action = ["sns:Publish"]
        Resource = [aws_sns_topic.order_notifications.arn]
      },
      {
        Sid    = "STSGetCallerIdentity"
        Effect = "Allow"
        Action = ["sts:GetCallerIdentity"]
        Resource = ["*"]
      }
    ]
  })
}

# ─── Payment Service Role ─────────────────────────────────────────────────────
resource "aws_iam_role" "payment_role" {
  name = "payment_service_role_guru"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "payment_logs" {
  role       = aws_iam_role.payment_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "payment_policy" {
  name = "payment-service-policy"
  role = aws_iam_role.payment_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadWriteOrders"
        Effect = "Allow"
        Action = ["dynamodb:GetItem", "dynamodb:UpdateItem"]
        Resource = [aws_dynamodb_table.orders_table.arn]
      },
      {
        Sid    = "SQSSendToFulfillment"
        Effect = "Allow"
        Action = ["sqs:SendMessage", "sqs:GetQueueUrl"]
        Resource = [aws_sqs_queue.order_processing.arn]
      },
      {
        Sid    = "SNSPublish"
        Effect = "Allow"
        Action = ["sns:Publish"]
        Resource = [aws_sns_topic.order_notifications.arn]
      },
      {
        Sid    = "STSGetCallerIdentity"
        Effect = "Allow"
        Action = ["sts:GetCallerIdentity"]
        Resource = ["*"]
      }
    ]
  })
}

# ─── Order Processor Role (SQS worker) ───────────────────────────────────────
resource "aws_iam_role" "processor_role" {
  name = "order_processor_role_guru"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "processor_logs" {
  role       = aws_iam_role.processor_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "processor_policy" {
  name = "order-processor-policy"
  role = aws_iam_role.processor_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadWriteOrders"
        Effect = "Allow"
        Action = ["dynamodb:GetItem", "dynamodb:PutItem"]
        Resource = [aws_dynamodb_table.orders_table.arn]
      },
      {
        Sid    = "SQSReceive"
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [aws_sqs_queue.order_processing.arn]
      },
      {
        Sid    = "SNSPublish"
        Effect = "Allow"
        Action = ["sns:Publish"]
        Resource = [aws_sns_topic.order_notifications.arn]
      },
      {
        Sid    = "STSGetCallerIdentity"
        Effect = "Allow"
        Action = ["sts:GetCallerIdentity"]
        Resource = ["*"]
      }
    ]
  })
}

# ─── Admin Service Role ───────────────────────────────────────────────────────
resource "aws_iam_role" "admin_role" {
  name = "admin_service_role_guru"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "admin_logs" {
  role       = aws_iam_role.admin_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "admin_policy" {
  name = "admin-service-policy"
  role = aws_iam_role.admin_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ProductsCRUD"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.products_table.arn,
          "${aws_dynamodb_table.products_table.arn}/index/*"
        ]
      },
      {
        Sid    = "OrdersReadUpdate"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.orders_table.arn,
          "${aws_dynamodb_table.orders_table.arn}/index/*"
        ]
      },
      {
        Sid    = "ReturnsManage"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.returns_table.arn,
          "${aws_dynamodb_table.returns_table.arn}/index/*"
        ]
      },
      {
        Sid    = "STSGetCallerIdentity"
        Effect = "Allow"
        Action = ["sts:GetCallerIdentity"]
        Resource = ["*"]
      }
    ]
  })
}
