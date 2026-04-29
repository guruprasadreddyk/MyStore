import json
import boto3
from utils import convert_decimal, response

dynamodb = boto3.resource("dynamodb")
product_table = dynamodb.Table("products_table_guru")


def lambda_handler(event, context):
    try:
        path = event.get("rawPath") or event.get("path", "")
        method = event.get("requestContext", {}).get("http", {}).get("method", "")

        # Strip /v1 prefix for backward compatibility
        if path.startswith("/v1/"):
            path = path[3:]  # Remove "/v1" prefix

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
                    if query.lower() in product.get("name", "").lower() or
                       query.lower() in product.get("description", "").lower()
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