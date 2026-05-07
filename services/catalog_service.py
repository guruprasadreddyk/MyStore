import json
import uuid
import boto3
from decimal import Decimal
from datetime import datetime
from boto3.dynamodb.conditions import Attr, Key
import os
from utils import convert_decimal, response, get_table_name

# ─── DynamoDB setup (lazy-loaded for testability) ────────────────────────────
def get_product_table():
    return boto3.resource("dynamodb").Table(get_table_name("products"))

def get_reviews_table():
    return boto3.resource("dynamodb").Table(get_table_name("reviews"))


# ─── Product helpers ──────────────────────────────────────────────────────────

def get_product_by_id(product_id):
    try:
        result = get_product_table().get_item(Key={"id": str(product_id)})
        item   = result.get("Item")
        return convert_decimal(item) if item else None
    except Exception as e:
        print(f"ERROR fetching product: {str(e)}")
        return None


def get_product_variants(product_id):
    """Get all variants for a product."""
    try:
        product = get_product_by_id(product_id)
        if not product:
            return None
        return product.get("variants", [])
    except Exception as e:
        print(f"ERROR fetching variants: {str(e)}")
        return None


def get_variant(product_id, variant_id):
    """Get specific variant by variant_id."""
    try:
        variants = get_product_variants(product_id)
        if not variants:
            return None
        for variant in variants:
            if variant.get("variant_id") == variant_id:
                return variant
        return None
    except Exception as e:
        print(f"ERROR fetching variant: {str(e)}")
        return None


def get_all_products(limit=10, last_key=None, min_price=None, max_price=None, category=None, sort_by=None):
    try:
        scan_kwargs = {"Limit": limit}
        if last_key:
            scan_kwargs["ExclusiveStartKey"] = last_key

        result = get_product_table().scan(**scan_kwargs)
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
        if not product_ids:
            return []

        # Batch-fetch all requested products in one DynamoDB call
        product_ids_str = [str(pid) for pid in product_ids]
        table_name = get_table_name("products")
        batch_result = boto3.resource("dynamodb").batch_get_item(
            RequestItems={
                table_name: {
                    "Keys": [{"id": pid} for pid in product_ids_str]
                }
            }
        )
        fetched = batch_result.get("Responses", {}).get(table_name, [])

        selected, categories, avg_price = [], set(), 0
        for p in fetched:
            p = convert_decimal(p)
            selected.append(p)
            categories.add(p.get("category", ""))
            avg_price += float(p.get("price", 0))

        if not selected:
            return []

        avg_price /= len(selected)

        # Paginate the scan to avoid truncation on large tables
        all_items = []
        scan_kwargs = {}
        while True:
            page = get_product_table().scan(**scan_kwargs)
            all_items.extend(page.get("Items", []))
            last_key = page.get("LastEvaluatedKey")
            if not last_key:
                break
            scan_kwargs["ExclusiveStartKey"] = last_key

        # Normalise product_ids to strings for safe membership check
        product_ids_set = {str(pid) for pid in product_ids}
        recs = []
        for p in all_items:
            if str(p.get("id", "")) not in product_ids_set:
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

def search_products(query, min_price=None, max_price=None, category=None, brand=None, min_rating=None, in_stock_only=False, last_key=None, limit=20):
    """
    Enhanced search with filters:
    - Uses category-price-index GSI for efficient category queries
    - Supports brand, rating, and stock availability filters
    - Text matching done in Python for case-insensitivity
    """
    try:
        query_lower = query.lower()
        results = []
        
        # If category specified, use GSI for efficient query
        if category and category != "All":
            query_kwargs = {
                "IndexName": "category-price-index",
                "KeyConditionExpression": Key("category").eq(category)
            }
            
            # Add price range to key condition if specified
            if min_price is not None and max_price is not None:
                query_kwargs["KeyConditionExpression"] = Key("category").eq(category) & Key("price").between(
                    Decimal(str(min_price)), Decimal(str(max_price))
                )
            elif min_price is not None:
                query_kwargs["KeyConditionExpression"] = Key("category").eq(category) & Key("price").gte(Decimal(str(min_price)))
            elif max_price is not None:
                query_kwargs["KeyConditionExpression"] = Key("category").eq(category) & Key("price").lte(Decimal(str(max_price)))
            
            if last_key:
                query_kwargs["ExclusiveStartKey"] = last_key
            
            page = get_product_table().query(**query_kwargs)
            items = page.get("Items", [])
            last_evaluated_key = page.get("LastEvaluatedKey")
        else:
            # No category filter - use scan with filters
            scan_kwargs = {}
            server_filter = None
            
            if min_price is not None:
                server_filter = Attr("price").gte(Decimal(str(min_price)))
            if max_price is not None:
                max_f = Attr("price").lte(Decimal(str(max_price)))
                server_filter = server_filter & max_f if server_filter else max_f
            
            if server_filter:
                scan_kwargs["FilterExpression"] = server_filter
            if last_key:
                scan_kwargs["ExclusiveStartKey"] = last_key
            
            page = get_product_table().scan(**scan_kwargs)
            items = page.get("Items", [])
            last_evaluated_key = page.get("LastEvaluatedKey")
        
        # Apply client-side filters
        for item in items:
            # Text search filter
            if query_lower and query_lower not in item.get("name", "").lower() and \
               query_lower not in item.get("description", "").lower():
                continue
            
            # Brand filter
            if brand and item.get("brand", "").lower() != brand.lower():
                continue
            
            # Rating filter
            if min_rating is not None:
                item_rating = float(item.get("rating", 0))
                if item_rating < float(min_rating):
                    continue
            
            # Stock availability filter
            if in_stock_only:
                stock = int(item.get("stock_quantity", 0))
                if stock <= 0:
                    continue
            
            results.append(convert_decimal(item))
            if len(results) >= limit:
                break
        
        return {
            "items": results,
            "lastEvaluatedKey": last_evaluated_key,
            "total": len(results)
        }
        
    except Exception as e:
        print(f"ERROR searching products: {str(e)}")
        return {"items": [], "lastEvaluatedKey": None, "total": 0}


# ─── Reviews helpers ──────────────────────────────────────────────────────────

def get_reviews_for_product(product_id, limit=20, last_key=None):
    """Get all reviews for a product, sorted by newest first."""
    try:
        kwargs = {
            "IndexName": "product_id-index",
            "KeyConditionExpression": Key("product_id").eq(str(product_id)),
            "Limit": limit,
            "ScanIndexForward": False  # Descending order (newest first)
        }
        if last_key:
            kwargs["ExclusiveStartKey"] = last_key
        
        result = get_reviews_table().query(**kwargs)
        return {
            "reviews": convert_decimal(result.get("Items", [])),
            "lastEvaluatedKey": result.get("LastEvaluatedKey")
        }
    except Exception as e:
        print(f"ERROR getting reviews: {str(e)}")
        return {"reviews": [], "lastEvaluatedKey": None}


def get_user_review_for_product(user_id, product_id):
    """Check if user already reviewed this product."""
    try:
        result = get_reviews_table().query(
            IndexName="user_id-index",
            KeyConditionExpression=Key("user_id").eq(user_id)
        )
        reviews = result.get("Items", [])
        for review in reviews:
            if review.get("product_id") == str(product_id):
                return convert_decimal(review)
        return None
    except Exception as e:
        print(f"ERROR checking user review: {str(e)}")
        return None


def has_user_ordered_product(user_id, product_id):
    """Check if user has ordered and received this product."""
    try:
        orders_table = boto3.resource("dynamodb").Table(get_table_name("orders"))
        
        # Query orders by user_id
        result = orders_table.query(
            IndexName="user_id-index",
            KeyConditionExpression=Key("user_id").eq(user_id)
        )
        
        orders = result.get("Items", [])
        
        # Check if any order contains this product and is delivered
        for order in orders:
            # Only allow reviews for delivered orders
            if order.get("status") in ["delivered", "shipped"]:
                items = order.get("items", [])
                for item in items:
                    if str(item.get("id")) == str(product_id):
                        return True
        
        return False
    except Exception as e:
        print(f"ERROR checking user orders: {str(e)}")
        return False


def create_review(user_id, user_email, product_id, rating, title, comment):
    """Create a new review and update product rating."""
    try:
        # Check if user has ordered this product
        if not has_user_ordered_product(user_id, product_id):
            return None, "You can only review products you have ordered and received"
        
        # Check if user already reviewed this product
        existing = get_user_review_for_product(user_id, product_id)
        if existing:
            return None, "You have already reviewed this product"
        
        # Validate rating
        if not (1 <= rating <= 5):
            return None, "Rating must be between 1 and 5"
        
        # Create review
        review = {
            "review_id": str(uuid.uuid4()),
            "product_id": str(product_id),
            "user_id": user_id,
            "user_email": user_email,
            "rating": rating,
            "title": title,
            "comment": comment,
            "helpful_count": 0,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
        get_reviews_table().put_item(Item=review)
        
        # Update product rating
        update_product_rating(product_id)
        
        return convert_decimal(review), None
    except Exception as e:
        print(f"ERROR creating review: {str(e)}")
        return None, str(e)


def update_product_rating(product_id):
    """Recalculate product rating from all reviews."""
    try:
        # Get all reviews for this product
        result = get_reviews_table().query(
            IndexName="product_id-index",
            KeyConditionExpression=Key("product_id").eq(str(product_id))
        )
        reviews = result.get("Items", [])
        
        if not reviews:
            return
        
        # Calculate average rating
        total_rating = sum(float(r.get("rating", 0)) for r in reviews)
        avg_rating = round(total_rating / len(reviews), 1)
        
        # Update product
        get_product_table().update_item(
            Key={"id": str(product_id)},
            UpdateExpression="SET rating = :rating, review_count = :count",
            ExpressionAttributeValues={
                ":rating": Decimal(str(avg_rating)),
                ":count": len(reviews)
            }
        )
        print(f"INFO: Updated product {product_id} rating to {avg_rating} ({len(reviews)} reviews)")
    except Exception as e:
        print(f"ERROR updating product rating: {str(e)}")


def mark_review_helpful(review_id):
    """Increment helpful count for a review."""
    try:
        get_reviews_table().update_item(
            Key={"review_id": review_id},
            UpdateExpression="SET helpful_count = helpful_count + :inc",
            ExpressionAttributeValues={":inc": 1}
        )
        return True
    except Exception as e:
        print(f"ERROR marking review helpful: {str(e)}")
        return False


def delete_review(review_id, user_id):
    """Delete a review (only by the author)."""
    try:
        # Get review to verify ownership and get product_id
        result = get_reviews_table().get_item(Key={"review_id": review_id})
        review = result.get("Item")
        
        if not review:
            return False, "Review not found"
        
        if review.get("user_id") != user_id:
            return False, "Not authorized to delete this review"
        
        product_id = review.get("product_id")
        
        # Delete review
        get_reviews_table().delete_item(Key={"review_id": review_id})
        
        # Update product rating
        update_product_rating(product_id)
        
        return True, None
    except Exception as e:
        print(f"ERROR deleting review: {str(e)}")
        return False, str(e)


# ─── Lambda handler ───────────────────────────────────────────────────────────

def lambda_handler(event, context):
    try:
        path   = event.get("rawPath") or event.get("path", "")
        method = event.get("requestContext", {}).get("http", {}).get("method", "")

        # Strip /v1 prefix for backward compatibility
        if path.startswith("/v1/"):
            path = path[3:]

        # Get user info from JWT (for authenticated routes)
        user_id = None
        user_email = None
        try:
            claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
            user_id = claims.get("sub")
            # Check namespaced claim first (set by Auth0 Action), fall back to standard claim
            user_email = claims.get("https://mystore.com/email") or claims.get("email")
        except Exception:
            pass

        print(f"INFO: Path={path}, Method={method}")

        # ── Health check ──────────────────────────────────────────────────────
        if path == "/health":
            return response(200, message="Catalog service is healthy")

        # ── GET /products ─────────────────────────────────────────────────────
        if path == "/products" and method == "GET":
            qp       = event.get("queryStringParameters") or {}
            limit    = int(qp.get("limit", 10))
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
        if path.startswith("/products/") and method == "GET" and "/reviews" not in path and "/variants" not in path:
            product_id = path.split("/")[-1]
            if not product_id:
                return response(400, message="Product ID is required")
            product = get_product_by_id(product_id)
            if not product:
                return response(404, message="Product not found.")
            return response(200, data=product)

        # ── GET /products/{id}/variants ───────────────────────────────────────
        if path.startswith("/products/") and "/variants" in path and method == "GET":
            parts = path.split("/")
            if len(parts) >= 4 and parts[3] == "variants":
                product_id = parts[2]
                if len(parts) == 4:
                    # GET /products/{id}/variants
                    variants = get_product_variants(product_id)
                    if variants is None:
                        return response(404, message="Product not found")
                    return response(200, data=variants)
                elif len(parts) == 5:
                    # GET /products/{id}/variants/{variant_id}
                    variant_id = parts[4]
                    variant = get_variant(product_id, variant_id)
                    if not variant:
                        return response(404, message="Variant not found")
                    return response(200, data=variant)

        # ── GET /products/{id}/reviews ────────────────────────────────────────
        if path.startswith("/products/") and path.endswith("/reviews") and method == "GET":
            product_id = path.split("/")[2]
            qp = event.get("queryStringParameters") or {}
            limit = int(qp.get("limit", 20))
            last_key = None
            if qp.get("lastEvaluatedKey"):
                try:
                    last_key = json.loads(qp["lastEvaluatedKey"])
                except Exception:
                    pass
            result = get_reviews_for_product(product_id, limit, last_key)
            return response(200, data=result)

        # ── POST /products/{id}/reviews ───────────────────────────────────────
        if path.startswith("/products/") and path.endswith("/reviews") and method == "POST":
            if not user_id:
                return response(401, message="Authentication required")
            
            product_id = path.split("/")[2]
            body = json.loads(event.get("body") or "{}")
            
            rating = body.get("rating")
            title = body.get("title", "")
            comment = body.get("comment", "")
            
            if not rating:
                return response(400, message="Rating is required")
            if not comment:
                return response(400, message="Comment is required")
            
            try:
                rating = int(rating)
            except (TypeError, ValueError):
                return response(400, message="Rating must be a number")
            
            review, error = create_review(user_id, user_email, product_id, rating, title, comment)
            if error:
                return response(400, message=error)
            
            return response(200, data=review, message="Review submitted successfully")

        # ── PUT /reviews/{id}/helpful ─────────────────────────────────────────
        if path.startswith("/reviews/") and path.endswith("/helpful") and method == "PUT":
            review_id = path.split("/")[2]
            success = mark_review_helpful(review_id)
            if success:
                return response(200, message="Marked as helpful")
            return response(500, message="Failed to mark as helpful")

        # ── DELETE /reviews/{id} ──────────────────────────────────────────────
        if path.startswith("/reviews/") and method == "DELETE":
            if not user_id:
                return response(401, message="Authentication required")
            
            review_id = path.split("/")[2]
            success, error = delete_review(review_id, user_id)
            if error:
                return response(400, message=error)
            
            return response(200, message="Review deleted successfully")

        # ── GET /recommendations ──────────────────────────────────────────────
        if path == "/recommendations" and method == "GET":
            qp          = event.get("queryStringParameters") or {}
            product_ids = qp.get("productIds", "")
            if not product_ids:
                return response(400, message="Product IDs are required for recommendations")
            try:
                limit = int(qp.get("limit", 5))
            except (ValueError, TypeError):
                limit = 5
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
            brand     = qp.get("brand")
            min_rating = float(qp["minRating"]) if qp.get("minRating") else None
            in_stock_only = qp.get("inStockOnly", "").lower() == "true"
            limit     = int(qp.get("limit", 20))
            last_key  = None
            if qp.get("lastEvaluatedKey"):
                try:
                    last_key = json.loads(qp["lastEvaluatedKey"])
                except Exception:
                    pass

            result = search_products(query, min_price, max_price, category, brand, min_rating, in_stock_only, last_key, limit)
            return response(200, data=result)

        return response(404, message="Route not found")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return response(500, message="Internal server error")
