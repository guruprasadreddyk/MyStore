import json
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Attr
import os
from utils import convert_decimal, response

# ─── DynamoDB setup ───────────────────────────────────────────────────────────
TABLE_NAME    = os.environ.get("PRODUCTS_TABLE", "products_table_guru")
dynamodb      = boto3.resource("dynamodb")
product_table = dynamodb.Table(TABLE_NAME)


# ─── Product helpers ──────────────────────────────────────────────────────────

def get_product_by_id(product_id):
    try:
        result = product_table.get_item(Key={"id": str(product_id)})
        item   = result.get("Item")
        return convert_decimal(item) if item else None
    except Exception as e:
        print(f"ERROR fetching product: {str(e)}")
        return None


def get_all_products(limit=8, last_key=None, min_price=None, max_price=None, category=None, sort_by=None):
    try:
        scan_kwargs = {"Limit": limit}
        if last_key:
            scan_kwargs["ExclusiveStartKey"] = last_key

        result = product_table.scan(**scan_kwargs)
        items  = result.get("Items", [])

        # Client-side filters (applied after DynamoDB page)
        if min_price is not None:
            items = [i for i in items if float(i.get("price", 0)) >= float(min_price)]
        if max_price is not None:
            items = [i for i in items if float(i.get("price", 0)) <= float(max_price)]
        if category and category != "All":
            items = [i for i in items if i.get("category", "").lower() == category.lower()]

        if sort_by == "price_low_high":
            items.sort(key=lambda x: float(x.get("price", 0)))
        elif sort_by == "price_high_low":
            items.sort(key=lambda x: float(x.get("price", 0)), reverse=True)

        return {
            "items":            convert_decimal(items),
            "lastEvaluatedKey": result.get("LastEvaluatedKey")
        }
    except Exception as e:
        print(f"ERROR scanning products: {str(e)}")
        return {"items": [], "lastEvaluatedKey": None}


def get_product_recommendations(product_ids, limit=5):
    try:
        selected, categories, avg_price = [], set(), 0

        for pid in product_ids:
            p = get_product_by_id(pid)
            if p:
                selected.append(p)
                categories.add(p.get("category", ""))
                avg_price += float(p.get("price", 0))

        if not selected:
            return []

        avg_price /= len(selected)

        all_items = product_table.scan().get("Items", [])
        recs = []
        for p in all_items:
            if p.get("id") not in product_ids:
                score = 0
                if p.get("category", "") in categories:
                    score += 10
                diff = abs(float(p.get("price", 0)) - avg_price)
                if diff < avg_price * 0.2:
                    score += 5
                elif diff < avg_price * 0.5:
                    score += 2
                score += float(p.get("rating", 0))
                p["recommendation_score"] = score
                recs.append(p)

        recs.sort(key=lambda x: x.get("recommendation_score", 0), reverse=True)
        return convert_decimal(recs[:limit])
    except Exception as e:
        print(f"ERROR getting recommendations: {str(e)}")
        return []


# ─── Search helpers ───────────────────────────────────────────────────────────

def search_products(query, min_price=None, max_price=None, category=None, last_key=None, limit=20):
    """
    Price/category filtered server-side via DynamoDB FilterExpression.
    Text matching done in Python for case-insensitivity (DynamoDB contains() is case-sensitive).
    """
    try:
        query_lower   = query.lower()
        server_filter = None

        if min_price is not None:
            server_filter = Attr("price").gte(Decimal(str(min_price)))
        if max_price is not None:
            max_f         = Attr("price").lte(Decimal(str(max_price)))
            server_filter = server_filter & max_f if server_filter else max_f
        if category and category != "All":
            cat_f         = Attr("category").eq(category)
            server_filter = server_filter & cat_f if server_filter else cat_f

        scan_kwargs = {}
        if server_filter:
            scan_kwargs["FilterExpression"] = server_filter
        if last_key:
            scan_kwargs["ExclusiveStartKey"] = last_key

        results, last_evaluated_key = [], None
        while True:
            page  = product_table.scan(**scan_kwargs)
            items = page.get("Items", [])

            for item in items:
                if query_lower in item.get("name", "").lower() or \
                   query_lower in item.get("description", "").lower():
                    results.append(convert_decimal(item))
                    if len(results) >= limit:
                        break

            last_evaluated_key = page.get("LastEvaluatedKey")
            if len(results) >= limit or not last_evaluated_key:
                break
            scan_kwargs["ExclusiveStartKey"] = last_evaluated_key

        return {"items": results, "lastEvaluatedKey": last_evaluated_key, "total": len(results)}
    except Exception as e:
        print(f"ERROR searching products: {str(e)}")
        return {"items": [], "lastEvaluatedKey": None, "total": 0}


# ─── Lambda handler ───────────────────────────────────────────────────────────

def lambda_handler(event, context):
    try:
        path   = event.get("rawPath") or event.get("path", "")
        method = event.get("requestContext", {}).get("http", {}).get("method", "")

        # Strip /v1 prefix for backward compatibility
        if path.startswith("/v1/"):
            path = path[3:]

        print(f"INFO: Path={path}, Method={method}")

        # ── Health check ──────────────────────────────────────────────────────
        if path == "/health":
            return response(200, message="Catalog service is healthy")

        # ── GET /products ─────────────────────────────────────────────────────
        if path == "/products" and method == "GET":
            qp       = event.get("queryStringParameters") or {}
            limit    = int(qp.get("limit", 8))
            last_key = None
            if qp.get("lastEvaluatedKey"):
                try:
                    last_key = json.loads(qp["lastEvaluatedKey"])
                except Exception:
                    pass
            result = get_all_products(
                limit    = limit,
                last_key = last_key,
                min_price= qp.get("minPrice"),
                max_price= qp.get("maxPrice"),
                category = qp.get("category"),
                sort_by  = qp.get("sortBy")
            )
            return response(200, data=result)

        # ── GET /products/{id} ────────────────────────────────────────────────
        if path.startswith("/products/") and method == "GET":
            product_id = path.split("/")[-1]
            if not product_id:
                return response(400, message="Product ID is required")
            product = get_product_by_id(product_id)
            if not product:
                return response(404, message="Product not found.")
            return response(200, data=product)

        # ── GET /recommendations ──────────────────────────────────────────────
        if path == "/recommendations" and method == "GET":
            qp          = event.get("queryStringParameters") or {}
            product_ids = qp.get("productIds", "")
            limit       = int(qp.get("limit", 5))
            if not product_ids:
                return response(400, message="Product IDs are required for recommendations")
            try:
                recs = get_product_recommendations(product_ids.split(","), limit)
                return response(200, data=recs)
            except Exception as e:
                return response(400, message=f"Invalid product IDs format: {str(e)}")

        # ── GET /search ───────────────────────────────────────────────────────
        if path == "/search" and method == "GET":
            qp    = event.get("queryStringParameters") or {}
            query = qp.get("q", "").strip()
            if not query:
                return response(400, message="Query parameter 'q' is required")

            min_price = Decimal(str(qp["minPrice"])) if qp.get("minPrice") else None
            max_price = Decimal(str(qp["maxPrice"])) if qp.get("maxPrice") else None
            category  = qp.get("category")
            limit     = int(qp.get("limit", 20))
            last_key  = None
            if qp.get("lastEvaluatedKey"):
                try:
                    last_key = json.loads(qp["lastEvaluatedKey"])
                except Exception:
                    pass

            result = search_products(query, min_price, max_price, category, last_key, limit)
            return response(200, data=result)

        return response(404, message="Route not found")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return response(500, message="Internal server error")
