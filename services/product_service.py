import json
import boto3
from decimal import Decimal
import os
from utils import convert_decimal, response

# 🔹 DynamoDB setup
TABLE_NAME = os.environ.get("PRODUCTS_TABLE", "products_table_guru")
dynamodb = boto3.resource("dynamodb")
product_table = dynamodb.Table(TABLE_NAME)

# Seeding logic moved to scripts/seed_products.py


# 🔹 Get single product
def get_product_by_id(product_id):
    try:

        result = product_table.get_item(Key={"id": str(product_id)})
        item = result.get("Item")

        return convert_decimal(item) if item else None

    except Exception as e:
        print(f"ERROR fetching product: {str(e)}")
        return None


# 🔹 Get all products with pagination, filtering, and sorting
def get_all_products(limit=8, last_key=None, min_price=None, max_price=None, category=None, sort_by=None):
    try:
        scan_kwargs = {"Limit": limit}
        if last_key:
            scan_kwargs["ExclusiveStartKey"] = last_key

        result = product_table.scan(**scan_kwargs)
        items = result.get("Items", [])
        
        # Apply filters
        if min_price is not None:
            items = [item for item in items if float(item.get("price", 0)) >= float(min_price)]
        if max_price is not None:
            items = [item for item in items if float(item.get("price", 0)) <= float(max_price)]
        if category and category != "All":
            items = [item for item in items if item.get("category", "").lower() == category.lower()]
        
        # Apply sorting
        if sort_by:
            if sort_by == "price_low_high":
                items.sort(key=lambda x: float(x.get("price", 0)))
            elif sort_by == "price_high_low":
                items.sort(key=lambda x: float(x.get("price", 0)), reverse=True)
        
        return {
            "items": convert_decimal(items),
            "lastEvaluatedKey": result.get("LastEvaluatedKey", None)
        }

    except Exception as e:
        print(f"ERROR scanning products: {str(e)}")
        return {"items": [], "lastEvaluatedKey": None}


# 🔹 Get product recommendations based on selected items
def get_product_recommendations(product_ids, limit=5):
    try:
        # Get the selected products to understand preferences
        selected_products = []
        categories = set()
        avg_price = 0
        
        for product_id in product_ids:
            product = get_product_by_id(product_id)
            if product:
                selected_products.append(product)
                categories.add(product.get("category", ""))
                avg_price += float(product.get("price", 0))
        
        if not selected_products:
            return []
            
        avg_price = avg_price / len(selected_products)
        
        # Get all products and filter out already selected ones
        all_products_result = product_table.scan()
        all_products = all_products_result.get("Items", [])
        
        # Filter out already selected products
        recommendations = []
        for product in all_products:
            if product.get("id") not in product_ids:
                # Score based on category match and price similarity
                score = 0
                
                # Category match (higher score for same category)
                if product.get("category", "") in categories:
                    score += 10
                
                # Price similarity (prefer similar price range)
                price_diff = abs(float(product.get("price", 0)) - avg_price)
                if price_diff < avg_price * 0.2:  # Within 20% of average price
                    score += 5
                elif price_diff < avg_price * 0.5:  # Within 50% of average price
                    score += 2
                
                # Rating bonus
                rating = float(product.get("rating", 0))
                score += rating
                
                product["recommendation_score"] = score
                recommendations.append(product)
        
        # Sort by recommendation score and return top results
        recommendations.sort(key=lambda x: x.get("recommendation_score", 0), reverse=True)
        
        return convert_decimal(recommendations[:limit])
        
    except Exception as e:
        print(f"ERROR getting recommendations: {str(e)}")
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
            query_params = event.get("queryStringParameters", {}) or {}
            
            limit = int(query_params.get("limit", 8))
            last_key_str = query_params.get("lastEvaluatedKey", None)
            min_price = query_params.get("minPrice", None)
            max_price = query_params.get("maxPrice", None)
            category = query_params.get("category", None)
            sort_by = query_params.get("sortBy", None)
            
            last_key = None
            if last_key_str:
                try:
                    last_key = json.loads(last_key_str)
                except:
                    pass

            result = get_all_products(limit, last_key, min_price, max_price, category, sort_by)
            return response(200, data=result)

        # 🔹 GET /recommendations
        if path == "/recommendations" and method == "GET":
            query_params = event.get("queryStringParameters", {}) or {}
            product_ids = query_params.get("productIds", "")
            limit = int(query_params.get("limit", 5))
            
            if not product_ids:
                return response(400, message="Product IDs are required for recommendations")
            
            try:
                product_ids = product_ids.split(",")
                recommendations = get_product_recommendations(product_ids, limit)
                return response(200, data=recommendations)
            except Exception as e:
                return response(400, message=f"Invalid product IDs format: {str(e)}")

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