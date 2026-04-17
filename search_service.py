import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
product_table = dynamodb.Table("products_table_guru")


def convert_decimal(obj):
    if isinstance(obj, list):
        return [convert_decimal(item) for item in obj]
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


def lambda_handler(event, context):
    try:
        path = event.get("rawPath") or event.get("path", "")
        method = event.get("requestContext", {}).get("http", {}).get("method", "")

        print(f"INFO: Path={path}, Method={method}")

        # 🔹 GET /search?q=query
        if path == "/search" and method == "GET":
            query_params = event.get("queryStringParameters", {})
            query = query_params.get("q", "").strip()

            if not query:
                return response(400, message="Query parameter 'q' is required")

            try:
                # Scan products and filter by name containing the query (case-insensitive)
                result = product_table.scan()
                products = result.get("Items", [])

                filtered_products = [
                    convert_decimal(product)
                    for product in products
                    if query.lower() in product.get("name", "").lower()
                ]

                return response(200, data=filtered_products)

            except Exception as e:
                print(f"ERROR scanning products: {str(e)}")
                return response(500, message="Error searching products")

        # 🔹 Invalid route
        return response(404, message="Route not found")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return response(500, message="Internal server error")