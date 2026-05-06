resource "aws_dynamodb_table" "cart_table" {
  name         = "cart_table_guru"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  # TTL: DynamoDB auto-deletes abandoned carts after 7 days (mimics Redis TTL)
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  # Point-in-time recovery: automatic daily backups
  point_in_time_recovery {
    enabled = true
  }
}

resource "aws_dynamodb_table" "products_table" {
  name         = "products_table_guru"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "category"
    type = "S"
  }

  attribute {
    name = "price"
    type = "N"
  }

  # GSI: allows efficient query by category (for category filtering)
  global_secondary_index {
    name            = "category-price-index"
    hash_key        = "category"
    range_key       = "price"
    projection_type = "ALL"
  }

  # Point-in-time recovery: automatic daily backups
  point_in_time_recovery {
    enabled = true
  }
}

resource "aws_dynamodb_table" "orders_table" {
  name         = "orders_table_guru"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "order_id"

  attribute {
    name = "order_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  # GSI: allows efficient query of all orders by user_id
  # Replaces the current full table scan + Python filter in get_all_orders()
  global_secondary_index {
    name            = "user_id-index"
    hash_key        = "user_id"
    projection_type = "ALL"
  }

  # Point-in-time recovery: automatic daily backups
  point_in_time_recovery {
    enabled = true
  }
}

resource "aws_dynamodb_table" "wishlist_table" {
  name         = "wishlist_table_guru"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  # Point-in-time recovery: automatic daily backups
  point_in_time_recovery {
    enabled = true
  }
}

resource "aws_dynamodb_table" "user_data_table" {
  name         = "user_data_table_guru"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  # Point-in-time recovery: automatic daily backups
  point_in_time_recovery {
    enabled = true
  }
}

resource "aws_dynamodb_table" "returns_table" {
  name         = "returns_table_guru"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "return_id"

  attribute {
    name = "return_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  # GSI: allows efficient query of returns by user_id
  global_secondary_index {
    name            = "user_id-index"
    hash_key        = "user_id"
    projection_type = "ALL"
  }

  # Point-in-time recovery: automatic daily backups
  point_in_time_recovery {
    enabled = true
  }
}

resource "aws_dynamodb_table" "reviews_table" {
  name         = "reviews_table_guru"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "review_id"

  attribute {
    name = "review_id"
    type = "S"
  }

  attribute {
    name = "product_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  # GSI: allows efficient query of all reviews for a product
  global_secondary_index {
    name            = "product_id-index"
    hash_key        = "product_id"
    projection_type = "ALL"
  }

  # GSI: allows efficient query of all reviews by a user
  global_secondary_index {
    name            = "user_id-index"
    hash_key        = "user_id"
    projection_type = "ALL"
  }

  # Point-in-time recovery: automatic daily backups
  point_in_time_recovery {
    enabled = true
  }
}
