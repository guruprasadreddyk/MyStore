import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('cart_table_guru')
product_table = dynamodb.Table('products_table_guru')

USER_ID = "user1"

def fetch_product(product_id):
    try:
        result = product_table.get_item(Key={"id": str(product_id)})
        item = result.get("Item")
        return convert_decimal(item) if item else None
    except Exception as e:
        print("ERROR fetching product:", str(e))
        return None

# 🔹 Helper: Convert Decimal → int
def convert_decimal(obj):
    if isinstance(obj, list):
        return [convert_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj)
    return obj


# 🔹 Helper: Standard response
def response(status_code, data=None, message=None):
    body = {
        "status": "success" if status_code < 400 else "error",
        "data": data,
        "message": message
    }
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT,DELETE"
        },
        "body": json.dumps(body)
    }


# 🔹 Helper: Get cart
def get_cart():
    res = table.get_item(Key={"user_id": USER_ID})
    return res.get("Item", {}).get("cart", [])


# 🔹 Helper: Save cart
def save_cart(cart):
    table.put_item(Item={
        "user_id": USER_ID,
        "cart": cart
    })


def lambda_handler(event, context):
    try:
        path = event.get("rawPath") or event.get("path", "")
        method = event.get("requestContext", {}).get("http", {}).get("method", "")

        # Strip /v1 prefix for backward compatibility
        if path.startswith("/v1/"):
            path = path[3:]  # Remove "/v1" prefix

        print(f"INFO: Path={path}, Method={method}")

        # 🔹 GET /cart
        if path == "/cart" and method == "GET":
            cart = convert_decimal(get_cart())
            return response(200, data=cart)

        # 🔹 POST /cart/add
        if path == "/cart/add" and method == "POST":
            body = json.loads(event.get("body") or "{}")

            allowed_fields = {"id"}
            extra_fields = set(body.keys()) - allowed_fields

            if extra_fields:
                return response(400, message=f"Unexpected fields: {list(extra_fields)}. Only 'id' is allowed")

            # validation
            product_id = str(body.get("id"))

            if not product_id:
                return response(400, message="Product ID required")

            product = fetch_product(product_id)

            if not product:
                return response(400, message="Invalid product")

            # Check stock availability
            current_stock = product.get("stock_quantity", 0)
            if current_stock <= 0:
                return response(400, message="Product is out of stock")

            # Check if adding this would exceed available stock
            cart = get_cart()
            current_quantity_in_cart = sum(
                item.get("quantity", 1) 
                for item in cart 
                if str(item.get("id")) == product_id
            )

            if current_quantity_in_cart >= current_stock:
                return response(400, message=f"Cannot add more of this item. Only {current_stock} available in stock")

            # override trusted values
            validated_item = {
                "id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "category": product.get("category", "General")
            }

            existing_item = next((item for item in cart if str(item.get("id")) == str(validated_item["id"])), None)

            if existing_item:
                existing_item["quantity"] += 1
            else:
                validated_item["quantity"] = 1
                cart.append(validated_item)
            save_cart(cart)

            return response(200, data=convert_decimal(cart), message="Item added")

        # 🔹 DELETE /cart/remove/{id}
        if path.startswith("/cart/remove/") and method == "DELETE":
            item_id = path.split("/")[-1]

            if not item_id:
                return response(400, message="Item ID required")

            cart = get_cart()
            item_found = False

            for item in cart:
                if str(item.get("id")) == str(item_id):
                    item_found = True
                    if item.get("quantity", 1) > 1:
                        item["quantity"] -= 1
                    else:
                        cart = [i for i in cart if str(i.get("id")) != str(item_id)]
                    break
                    
            if not item_found:
                return response(404, message="Item not found in cart")

            save_cart(cart)

            return response(200, data=convert_decimal(cart), message="Item removed")

        # 🔹 DELETE /cart → clear entire cart
        if path == "/cart" and method == "DELETE":
            save_cart([])
            return response(200, message="Cart cleared")

        # 🔹 Invalid route
        return response(404, message="Route not found")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return response(500, message="Internal server error")