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
}

resource "aws_dynamodb_table" "products_table" {
  name         = "products_table_guru"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
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
}

resource "aws_dynamodb_table" "wishlist_table" {
  name         = "wishlist_table_guru"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"

  attribute {
    name = "user_id"
    type = "S"
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
}
