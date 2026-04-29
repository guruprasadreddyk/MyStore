import json
import boto3
from decimal import Decimal
from utils import convert_decimal, response, get_user_id

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('wishlist_table_guru')
product_table = dynamodb.Table('products_table_guru')

def fetch_product(product_id):
    try:
        result = product_table.get_item(Key={"id": str(product_id)})
        item = result.get("Item")
        return convert_decimal(item) if item else None
    except Exception as e:
        print("ERROR fetching product:", str(e))
        return None

# 🔹 Helper: Get wishlist
def get_wishlist(user_id):
    res = table.get_item(Key={"user_id": user_id})
    return res.get("Item", {}).get("wishlist", [])

# 🔹 Helper: Save wishlist
def save_wishlist(user_id, wishlist):
    table.put_item(Item={
        "user_id": user_id,
        "wishlist": wishlist
    })

def lambda_handler(event, context):
    try:
        user_id = get_user_id(event)
        path = event.get("rawPath") or event.get("path", "")
        method = event.get("requestContext", {}).get("http", {}).get("method", "")

        # Strip /v1 prefix for backward compatibility
        if path.startswith("/v1/"):
            path = path[3:]

        print(f"INFO: Path={path}, Method={method}, User={user_id}")

        # 🔹 GET /wishlist
        if path == "/wishlist" and method == "GET":
            wishlist = convert_decimal(get_wishlist(user_id))
            return response(200, data=wishlist)

        # 🔹 POST /wishlist/add
        if path == "/wishlist/add" and method == "POST":
            body = json.loads(event.get("body") or "{}")

            allowed_fields = {"id"}
            extra_fields = set(body.keys()) - allowed_fields

            if extra_fields:
                return response(400, message=f"Unexpected fields: {list(extra_fields)}. Only 'id' is allowed")

            product_id = str(body.get("id"))
            if not product_id:
                return response(400, message="Product ID required")

            product = fetch_product(product_id)
            if not product:
                return response(400, message="Invalid product")

            wishlist = get_wishlist(user_id)
            
            # Check if already in wishlist
            existing_item = next((item for item in wishlist if str(item.get("id")) == str(product_id)), None)

            if existing_item:
                return response(400, message="Item already in wishlist")
            
            validated_item = {
                "id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "category": product.get("category", "General"),
                "image_url": product.get("image_url", "https://via.placeholder.com/150")
            }

            wishlist.append(validated_item)
            save_wishlist(user_id, wishlist)

            return response(200, data=convert_decimal(wishlist), message="Item added to wishlist")

        # 🔹 DELETE /wishlist/remove/{id}
        if path.startswith("/wishlist/remove/") and method == "DELETE":
            item_id = path.split("/")[-1]

            if not item_id:
                return response(400, message="Item ID required")

            wishlist = get_wishlist(user_id)
            
            # Filter out the item
            new_wishlist = [i for i in wishlist if str(i.get("id")) != str(item_id)]
            
            if len(new_wishlist) == len(wishlist):
                return response(404, message="Item not found in wishlist")

            save_wishlist(user_id, new_wishlist)

            return response(200, data=convert_decimal(new_wishlist), message="Item removed from wishlist")

        # 🔹 Invalid route
        return response(404, message="Route not found")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return response(500, message="Internal server error")
