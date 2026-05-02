import json
import boto3
import time
from decimal import Decimal
from utils import convert_decimal, response, get_user_id

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('cart_table_guru')
product_table = dynamodb.Table('products_table_guru')

# Cart TTL: 7 days of inactivity before auto-expiry (mimics Redis TTL behaviour)
CART_TTL_SECONDS = 7 * 24 * 60 * 60


def fetch_product(product_id):
    try:
        result = product_table.get_item(Key={"id": str(product_id)})
        item = result.get("Item")
        return convert_decimal(item) if item else None
    except Exception as e:
        print("ERROR fetching product:", str(e))
        return None


# 🔹 Helper: Get cart
def get_cart(user_id):
    res = table.get_item(Key={"user_id": user_id})
    return res.get("Item", {}).get("cart", [])


# 🔹 Helper: Save cart with refreshed TTL on every write
def save_cart(user_id, cart):
    table.put_item(Item={
        "user_id": user_id,
        "cart": cart,
        "ttl": int(time.time()) + CART_TTL_SECONDS  # auto-expire after 7 days of inactivity
    })


def lambda_handler(event, context):
    try:
        user_id = get_user_id(event)
        path = event.get("rawPath") or event.get("path", "")
        method = event.get("requestContext", {}).get("http", {}).get("method", "")

        # Strip /v1 prefix for backward compatibility
        if path.startswith("/v1/"):
            path = path[3:]  # Remove "/v1" prefix

        print(f"INFO: Path={path}, Method={method}, User={user_id}")

        # 🔹 GET /cart
        if path == "/cart" and method == "GET":
            cart = convert_decimal(get_cart(user_id))
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
            cart = get_cart(user_id)
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
            save_cart(user_id, cart)

            return response(200, data=convert_decimal(cart), message="Item added")

        # 🔹 DELETE /cart/remove/{id}
        if path.startswith("/cart/remove/") and method == "DELETE":
            item_id = path.split("/")[-1]

            if not item_id:
                return response(400, message="Item ID required")

            cart = get_cart(user_id)
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

            save_cart(user_id, cart)

            return response(200, data=convert_decimal(cart), message="Item removed")

        # 🔹 DELETE /cart → clear entire cart
        if path == "/cart" and method == "DELETE":
            save_cart(user_id, [])
            return response(200, message="Cart cleared")

        # 🔹 Invalid route
        return response(404, message="Route not found")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return response(500, message="Internal server error")