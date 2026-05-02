import json
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Attr
from utils import convert_decimal, response

dynamodb = boto3.resource("dynamodb")
product_table = dynamodb.Table("products_table_guru")


def search_products(query, min_price=None, max_price=None, category=None, last_key=None, limit=20):
    """
    Server-side filtered search using DynamoDB FilterExpression.
    Falls back to case-insensitive post-filter for text matching since
    DynamoDB FilterExpression is case-sensitive.
    """
    try:
        query_lower = query.lower()

        # Price and category filters are applied server-side in DynamoDB (reliable, exact).
        # Text matching is intentionally done in Python after the scan — DynamoDB
        # contains() is case-sensitive and would miss "HEADPHONES" vs "Headphones".
        server_filter = None
        if min_price is not None:
            server_filter = Attr("price").gte(Decimal(str(min_price)))
        if max_price is not None:
            max_f = Attr("price").lte(Decimal(str(max_price)))
            server_filter = server_filter & max_f if server_filter else max_f
        if category and category != "All":
            cat_f = Attr("category").eq(category)
            server_filter = server_filter & cat_f if server_filter else cat_f

        results = []
        scan_kwargs = {}
        if server_filter:
            scan_kwargs["FilterExpression"] = server_filter
        if last_key:
            scan_kwargs["ExclusiveStartKey"] = last_key

        # Paginate and apply case-insensitive text match in Python
        last_evaluated_key = None
        while True:
            page = product_table.scan(**scan_kwargs)
            items = page.get("Items", [])

            for item in items:
                name = item.get("name", "").lower()
                description = item.get("description", "").lower()
                if query_lower in name or query_lower in description:
                    results.append(convert_decimal(item))
                    if len(results) >= limit:
                        break

            last_evaluated_key = page.get("LastEvaluatedKey")

            if len(results) >= limit or not last_evaluated_key:
                break

            scan_kwargs["ExclusiveStartKey"] = last_evaluated_key

        return {
            "items": results,
            "lastEvaluatedKey": last_evaluated_key,
            "total": len(results)
        }

    except Exception as e:
        print(f"ERROR searching products: {str(e)}")
        return {"items": [], "lastEvaluatedKey": None, "total": 0}


def lambda_handler(event, context):
    try:
        path = event.get("rawPath") or event.get("path", "")
        method = event.get("requestContext", {}).get("http", {}).get("method", "")

        # Strip /v1 prefix for backward compatibility
        if path.startswith("/v1/"):
            path = path[3:]

        print(f"INFO: Path={path}, Method={method}")

        # 🔹 GET /search
        if path == "/search" and method == "GET":
            query_params = event.get("queryStringParameters") or {}
            query = query_params.get("q", "").strip()

            if not query:
                return response(400, message="Query parameter 'q' is required")

            # Optional filters
            min_price  = query_params.get("minPrice")
            max_price  = query_params.get("maxPrice")
            category   = query_params.get("category")
            limit      = int(query_params.get("limit", 20))
            last_key_str = query_params.get("lastEvaluatedKey")

            last_key = None
            if last_key_str:
                try:
                    last_key = json.loads(last_key_str)
                except Exception:
                    pass

            # Convert price params to Decimal for DynamoDB FilterExpression compatibility
            min_price = Decimal(str(min_price)) if min_price else None
            max_price = Decimal(str(max_price)) if max_price else None

            result = search_products(query, min_price, max_price, category, last_key, limit)
            return response(200, data=result)

        # 🔹 Invalid route
        return response(404, message="Route not found")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return response(500, message="Internal server error")