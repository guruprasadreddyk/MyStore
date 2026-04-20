import json
import boto3
from decimal import Decimal
import os

# 🔹 DynamoDB setup
TABLE_NAME = os.environ.get("PRODUCTS_TABLE", "products_table_guru")
dynamodb = boto3.resource("dynamodb")
product_table = dynamodb.Table(TABLE_NAME)

# 🔹 Default seed data
default_products = [
    {
        "id": "1",
        "name": "All That We See or Seem",
        "price": 5000,
        "category": "Books",
        "stock_quantity": 15,
        "description": "A captivating novel exploring the depths of human perception and reality.",
        "rating": 4.5
    },
    {
        "id": "2",
        "name": "All The Way to the River",
        "price": 2000,
        "category": "Books",
        "stock_quantity": 8,
        "description": "An adventurous tale of self-discovery and the journey of life.",
        "rating": 4.2
    },
    {
        "id": "3",
        "name": "The Antidote",
        "price": 3000,
        "category": "Books",
        "stock_quantity": 12,
        "description": "A philosophical exploration of happiness and the human condition.",
        "rating": 4.7
    },
    {
        "id": "4",
        "name": "Atmosphere",
        "price": 2100,
        "category": "Books",
        "stock_quantity": 20,
        "description": "A scientific journey through Earth's atmosphere and climate.",
        "rating": 4.3
    },
    {
        "id": "5",
        "name": "Audition",
        "price": 3500,
        "category": "Books",
        "stock_quantity": 6,
        "description": "A thrilling story about ambition, talent, and the entertainment industry.",
        "rating": 4.1
    },
    {
        "id": "6",
        "name": "Wireless Bluetooth Headphones",
        "price": 15000,
        "category": "Electronics",
        "stock_quantity": 25,
        "description": "Premium noise-cancelling wireless headphones with 30-hour battery life.",
        "rating": 4.6
    },
    {
        "id": "7",
        "name": "Smart Fitness Watch",
        "price": 25000,
        "category": "Electronics",
        "stock_quantity": 10,
        "description": "Advanced fitness tracker with heart rate monitoring and GPS.",
        "rating": 4.4
    },
    {
        "id": "8",
        "name": "Organic Cotton T-Shirt",
        "price": 2500,
        "category": "Clothing",
        "stock_quantity": 50,
        "description": "Comfortable, eco-friendly t-shirt made from 100% organic cotton.",
        "rating": 4.0
    },
    {
        "id": "9",
        "name": "Ceramic Coffee Mug",
        "price": 800,
        "category": "Home & Kitchen",
        "stock_quantity": 30,
        "description": "Handcrafted ceramic mug perfect for your morning coffee ritual.",
        "rating": 4.2
    },
    {
        "id": "10",
        "name": "Yoga Mat Premium",
        "price": 4500,
        "category": "Sports & Fitness",
        "stock_quantity": 18,
        "description": "Non-slip, eco-friendly yoga mat with excellent cushioning.",
        "rating": 4.5
    },
    {
        "id": "11",
        "name": "Stainless Steel Water Bottle",
        "price": 1200,
        "category": "Home & Kitchen",
        "stock_quantity": 40,
        "description": "Insulated stainless steel bottle that keeps drinks cold for 24 hours.",
        "rating": 4.3
    },
    {
        "id": "12",
        "name": "Wireless Charging Pad",
        "price": 3000,
        "category": "Electronics",
        "stock_quantity": 22,
        "description": "Fast wireless charging pad compatible with all Qi-enabled devices.",
        "rating": 4.1
    }
]

# 🔹 Convert Decimal to int/float for JSON response
def convert_decimal(obj):
    if isinstance(obj, list):
        return [convert_decimal(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


# 🔹 Standard API response
def response(status_code, data=None, message=None):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT,DELETE"
        },
        "body": json.dumps({
            "status": "success" if status_code < 400 else "error",
            "data": data,
            "message": message
        })
    }


# 🔹 Seed data (runs only if table empty)
def seed_products():
    try:
        print("Checking if table is empty...")

        result = product_table.scan(ProjectionExpression="id", Limit=1)

        if result.get("Count", 0) == 0:
            print("Table empty → seeding data...")

            with product_table.batch_writer() as batch:
                for product in default_products:
                    batch.put_item(Item={
                        "id": str(product["id"]),
                        "name": product["name"],
                        "price": int(product["price"]),
                        "category": product["category"],
                        "stock_quantity": int(product["stock_quantity"]),
                        "description": product["description"],
                        "rating": Decimal(str(product["rating"]))  # ✅ FIXED
                    })

            print("Seeding completed ✅")
        else:
            print("Table already has data, skipping seeding")

    except Exception as e:
        print(f"ERROR seeding products: {str(e)}")


# 🔹 Get single product
def get_product_by_id(product_id):
    try:
        seed_products()

        result = product_table.get_item(Key={"id": str(product_id)})
        item = result.get("Item")

        return convert_decimal(item) if item else None

    except Exception as e:
        print(f"ERROR fetching product: {str(e)}")
        return None


# 🔹 Get all products
def get_all_products():
    try:
        seed_products()

        result = product_table.scan()
        return convert_decimal(result.get("Items", []))

    except Exception as e:
        print(f"ERROR scanning products: {str(e)}")
        return []


# 🔹 Lambda handler
def lambda_handler(event, context):
    try:
        print("Incoming event:", json.dumps(event))

        path = event.get("rawPath") or event.get("path", "")
        method = event.get("requestContext", {}).get("http", {}).get("method", "")

        # Strip /v1 prefix for backward compatibility
        if path.startswith("/v1/"):
            path = path[3:]  # Remove "/v1" prefix

        print(f"Path={path}, Method={method}")

        # 🔹 Health check
        if path == "/health":
            return response(200, message="Product service is healthy")

        # 🔹 GET /products
        if path == "/products" and method == "GET":
            products = get_all_products()
            return response(200, data=products)

        # 🔹 GET /products/{id}
        if path.startswith("/products/") and method == "GET":
            product_id = path.split("/")[-1]

            if not product_id:
                return response(400, message="Product ID is required")

            product = get_product_by_id(product_id)

            if not product:
                return response(404, message="Product not found.")

            return response(200, data=product)

        return response(404, message="Route not found")
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return response(500, message="Internal server error")