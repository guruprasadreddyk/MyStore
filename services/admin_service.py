import json
import boto3
from decimal import Decimal
from datetime import datetime
from boto3.dynamodb.conditions import Attr
from utils import convert_decimal, response, update_order_status
from validation import validate


# Lazy-load tables for better testability
def get_products_table():
    return boto3.resource("dynamodb").Table("products_table_guru")

def get_orders_table():
    return boto3.resource("dynamodb").Table("orders_table_guru")

def get_returns_table():
    return boto3.resource("dynamodb").Table("returns_table_guru")


# ─── Auth guard ───────────────────────────────────────────────────────────────

def is_admin(event):
    """
    Check Auth0 JWT custom claim for admin role.
    Add custom claim in Auth0 dashboard:
      Actions → Flows → Login → add { "https://mystore.com/roles": ["admin"] }
    """
    try:
        claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
        roles  = claims.get("https://mystore.com/roles", "")
        # JWT claims are strings; handle both list and comma-separated string
        if isinstance(roles, list):
            return "admin" in roles
        return "admin" in str(roles)
    except (KeyError, TypeError):
        return False


# ─── Dashboard stats ──────────────────────────────────────────────────────────

def get_dashboard_stats():
    try:
        # All orders
        orders_result = get_orders_table().scan()
        orders        = orders_result.get("Items", [])

        total_orders   = len(orders)
        total_revenue  = sum(
            sum(float(i.get("price", 0)) * int(i.get("quantity", 1)) for i in o.get("items", []))
            for o in orders
        )

        # Orders by status
        status_counts = {}
        for o in orders:
            s = o.get("status", "unknown")
            status_counts[s] = status_counts.get(s, 0) + 1

        # Low stock products (stock_quantity < 10)
        products_result = get_products_table().scan(
            FilterExpression=Attr("stock_quantity").lt(10)
        )
        low_stock = convert_decimal(products_result.get("Items", []))

        # Top 5 products by order frequency
        product_counts = {}
        for o in orders:
            for item in o.get("items", []):
                pid = str(item.get("id", ""))
                qty = int(item.get("quantity", 1))
                product_counts[pid] = product_counts.get(pid, 0) + qty

        top_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Time-series data (last 30 days)
        from collections import defaultdict
        daily_stats = defaultdict(lambda: {"orders": 0, "revenue": 0, "customers": set()})
        
        for o in orders:
            created_at = o.get("created_at", "")
            if created_at:
                # Extract date (YYYY-MM-DD) from ISO timestamp
                date = created_at.split("T")[0]
                order_total = sum(float(i.get("price", 0)) * int(i.get("quantity", 1)) for i in o.get("items", []))
                
                daily_stats[date]["orders"] += 1
                daily_stats[date]["revenue"] += order_total
                daily_stats[date]["customers"].add(o.get("user_id", ""))
        
        # Convert to sorted list (last 30 days)
        from datetime import datetime, timedelta
        today = datetime.utcnow().date()
        time_series = []
        
        for i in range(29, -1, -1):  # Last 30 days
            date = (today - timedelta(days=i)).isoformat()
            stats = daily_stats.get(date, {"orders": 0, "revenue": 0, "customers": set()})
            time_series.append({
                "date": date,
                "orders": stats["orders"],
                "revenue": round(stats["revenue"], 2),
                "customers": len(stats["customers"])
            })

        return {
            "total_orders":   total_orders,
            "total_revenue":  round(total_revenue, 2),
            "status_counts":  status_counts,
            "low_stock":      low_stock,
            "top_products":   [{"product_id": pid, "units_sold": qty} for pid, qty in top_products],
            "time_series":    time_series
        }
    except Exception as e:
        print(f"ERROR getting dashboard stats: {str(e)}")
        return {}


# ─── Product management ───────────────────────────────────────────────────────

def get_all_products_admin():
    """Full scan — no pagination limit, for admin view."""
    try:
        items = []
        result = get_products_table().scan()
        items.extend(result.get("Items", []))
        while result.get("LastEvaluatedKey"):
            result = get_products_table().scan(ExclusiveStartKey=result["LastEvaluatedKey"])
            items.extend(result.get("Items", []))
        return convert_decimal(items)
    except Exception as e:
        print(f"ERROR fetching all products: {str(e)}")
        return []


def update_product(product_id, updates):
    """
    Update allowed product fields: price, stock_quantity, name, description.
    Returns updated product.
    """
    allowed = {"price", "stock_quantity", "name", "description"}
    filtered = {k: v for k, v in updates.items() if k in allowed}

    if not filtered:
        return None, "No valid fields to update"

    # Validate numeric fields
    if "price" in filtered:
        try:
            price = float(filtered["price"])
        except (TypeError, ValueError):
            return None, "price must be a number"
        if price < 0:
            return None, "price cannot be negative"
        filtered["price"] = Decimal(str(price))

    if "stock_quantity" in filtered:
        try:
            stock = int(filtered["stock_quantity"])
        except (TypeError, ValueError):
            return None, "stock_quantity must be an integer"
        if stock < 0:
            return None, "stock_quantity cannot be negative"
        filtered["stock_quantity"] = stock

    update_expr   = "SET " + ", ".join(f"#{k} = :{k}" for k in filtered)
    expr_names    = {f"#{k}": k for k in filtered}
    expr_values   = {f":{k}": (str(v) if k in ("name", "description") else v) for k, v in filtered.items()}

    try:
        result = get_products_table().update_item(
            Key={"id": str(product_id)},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ReturnValues="ALL_NEW"
        )
        return convert_decimal(result.get("Attributes", {})), None
    except Exception as e:
        print(f"ERROR updating product: {str(e)}")
        return None, str(e)


def add_product(data):
    """Add a new product. Requires: id, name, price, category, stock_quantity, description, rating."""
    required = {"id", "name", "price", "category", "stock_quantity", "description", "rating"}
    missing  = required - set(data.keys())
    if missing:
        return None, f"Missing required fields: {list(missing)}"
    try:
        item = {
            "id":             str(data["id"]),
            "name":           str(data["name"]),
            "price":          int(data["price"]),
            "category":       str(data["category"]),
            "stock_quantity": int(data["stock_quantity"]),
            "description":    str(data["description"]),
            "rating":         Decimal(str(data["rating"])),
            "review_count":   int(data.get("review_count", 0))
        }
        get_products_table().put_item(Item=item)
        return convert_decimal(item), None
    except Exception as e:
        print(f"ERROR adding product: {str(e)}")
        return None, str(e)


def delete_product(product_id):
    try:
        get_products_table().delete_item(Key={"id": str(product_id)})
        return True
    except Exception as e:
        print(f"ERROR deleting product: {str(e)}")
        return False


# ─── Order management ─────────────────────────────────────────────────────────

def get_all_orders_admin(status_filter=None):
    """Full scan of all orders across all users."""
    try:
        kwargs = {}
        if status_filter:
            kwargs["FilterExpression"] = Attr("status").eq(status_filter)
        items  = []
        result = get_orders_table().scan(**kwargs)
        items.extend(result.get("Items", []))
        while result.get("LastEvaluatedKey"):
            kwargs["ExclusiveStartKey"] = result["LastEvaluatedKey"]
            result = get_orders_table().scan(**kwargs)
            items.extend(result.get("Items", []))
        return convert_decimal(items)
    except Exception as e:
        print(f"ERROR fetching all orders: {str(e)}")
        return []


def update_order_status_admin(order_id, new_status):
    valid_statuses = {"created", "confirmed", "processing", "shipped", "delivered", "cancelled", "paid"}
    if new_status not in valid_statuses:
        return None, f"Invalid status. Must be one of: {list(valid_statuses)}"
    try:
        result = get_orders_table().update_item(
            Key={"order_id": str(order_id)},
            UpdateExpression="SET #s = :status",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":status": new_status},
            ReturnValues="ALL_NEW"
        )
        return convert_decimal(result.get("Attributes", {})), None
    except Exception as e:
        print(f"ERROR updating order status: {str(e)}")
        return None, str(e)


# ─── Return management ────────────────────────────────────────────────────────

def get_all_returns_admin(status_filter=None):
    """Get all return requests."""
    try:
        kwargs = {}
        if status_filter:
            kwargs["FilterExpression"] = Attr("status").eq(status_filter)
        items  = []
        result = get_returns_table().scan(**kwargs)
        items.extend(result.get("Items", []))
        while result.get("LastEvaluatedKey"):
            kwargs["ExclusiveStartKey"] = result["LastEvaluatedKey"]
            result = get_returns_table().scan(**kwargs)
            items.extend(result.get("Items", []))
        return convert_decimal(items)
    except Exception as e:
        print(f"ERROR fetching returns: {str(e)}")
        return []


def approve_return_admin(return_id):
    """Approve a return request."""
    try:
        result = get_returns_table().update_item(
            Key={"return_id": str(return_id)},
            UpdateExpression="SET #s = :status, approved_at = :now",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":status": "approved",
                ":now": datetime.utcnow().isoformat() + "Z"
            },
            ReturnValues="ALL_NEW"
        )
        
        return_req = result.get("Attributes", {})
        
        # Update order status to return_approved
        order_id = return_req.get("order_id")
        if order_id:
            update_order_status(order_id, "return_approved")
        
        return convert_decimal(return_req), None
    except Exception as e:
        print(f"ERROR approving return: {str(e)}")
        return None, str(e)


def reject_return_admin(return_id, reason=None):
    """Reject a return request."""
    try:
        update_expr = "SET #s = :status, rejected_at = :now"
        expr_values = {
            ":status": "rejected",
            ":now": datetime.utcnow().isoformat() + "Z"
        }
        
        if reason:
            update_expr += ", rejection_reason = :reason"
            expr_values[":reason"] = str(reason)
        
        result = get_returns_table().update_item(
            Key={"return_id": str(return_id)},
            UpdateExpression=update_expr,
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues=expr_values,
            ReturnValues="ALL_NEW"
        )
        
        return_req = result.get("Attributes", {})
        
        # Update order status to return_rejected
        order_id = return_req.get("order_id")
        if order_id:
            update_order_status(order_id, "return_rejected")
        
        return convert_decimal(return_req), None
    except Exception as e:
        print(f"ERROR rejecting return: {str(e)}")
        return None, str(e)


def process_refund_admin(return_id):
    """Process refund for an approved return."""
    try:
        result = get_returns_table().update_item(
            Key={"return_id": str(return_id)},
            UpdateExpression="SET #s = :status, refund_status = :refund, refunded_at = :now",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":status": "refunded",
                ":refund": "completed",
                ":now": datetime.utcnow().isoformat() + "Z"
            },
            ReturnValues="ALL_NEW"
        )
        
        return_req = result.get("Attributes", {})
        
        # Update order status to refunded
        order_id = return_req.get("order_id")
        if order_id:
            update_order_status(order_id, "refunded")
        
        return convert_decimal(return_req), None
    except Exception as e:
        print(f"ERROR processing refund: {str(e)}")
        return None, str(e)


# ─── Lambda handler ───────────────────────────────────────────────────────────

def lambda_handler(event, context):
    try:
        path   = event.get("rawPath") or event.get("path", "")
        method = event.get("requestContext", {}).get("http", {}).get("method", "")

        if path.startswith("/v1/"):
            path = path[3:]

        print(f"INFO: Admin Path={path}, Method={method}")

        # All admin routes require admin role
        if not is_admin(event):
            return response(403, message="Forbidden: admin access required")

        # ── GET /admin/dashboard ──────────────────────────────────────────────
        if path == "/admin/dashboard" and method == "GET":
            return response(200, data=get_dashboard_stats())

        # ── GET /admin/products ───────────────────────────────────────────────
        if path == "/admin/products" and method == "GET":
            return response(200, data=get_all_products_admin())

        # ── POST /admin/products ──────────────────────────────────────────────
        if path == "/admin/products" and method == "POST":
            body = json.loads(event.get("body") or "{}")
            
            # Validate input
            try:
                validate(body, "add_product")
            except ValueError as e:
                return response(400, message=str(e))
            
            product, err = add_product(body)
            if err:
                return response(400, message=err)
            return response(200, data=product, message="Product added")

        # ── PUT /admin/products/{id} ──────────────────────────────────────────
        if path.startswith("/admin/products/") and method == "PUT":
            product_id = path.split("/")[-1]
            body       = json.loads(event.get("body") or "{}")
            updated, err = update_product(product_id, body)
            if err:
                return response(400, message=err)
            return response(200, data=updated, message="Product updated")

        # ── DELETE /admin/products/{id} ───────────────────────────────────────
        if path.startswith("/admin/products/") and method == "DELETE":
            product_id = path.split("/")[-1]
            ok = delete_product(product_id)
            if not ok:
                return response(500, message="Failed to delete product")
            return response(200, message=f"Product {product_id} deleted")

        # ── GET /admin/orders ─────────────────────────────────────────────────
        if path == "/admin/orders" and method == "GET":
            qp     = event.get("queryStringParameters") or {}
            status = qp.get("status")
            return response(200, data=get_all_orders_admin(status))

        # ── PUT /admin/orders/{id} ────────────────────────────────────────────
        if path.startswith("/admin/orders/") and method == "PUT":
            order_id   = path.split("/")[-1]
            body       = json.loads(event.get("body") or "{}")
            new_status = body.get("status")
            if not new_status:
                return response(400, message="status is required")
            updated, err = update_order_status_admin(order_id, new_status)
            if err:
                return response(400, message=err)
            return response(200, data=updated, message="Order status updated")

        # ── GET /admin/returns ────────────────────────────────────────────────
        if path == "/admin/returns" and method == "GET":
            qp     = event.get("queryStringParameters") or {}
            status = qp.get("status")
            return response(200, data=get_all_returns_admin(status))

        # ── PUT /admin/returns/{id}/approve ───────────────────────────────────
        if path.startswith("/admin/returns/") and "/approve" in path and method == "PUT":
            return_id = path.split("/")[3]
            updated, err = approve_return_admin(return_id)
            if err:
                return response(400, message=err)
            return response(200, data=updated, message="Return approved")

        # ── PUT /admin/returns/{id}/reject ────────────────────────────────────
        if path.startswith("/admin/returns/") and "/reject" in path and method == "PUT":
            return_id = path.split("/")[3]
            body = json.loads(event.get("body") or "{}")
            reason = body.get("reason")
            updated, err = reject_return_admin(return_id, reason)
            if err:
                return response(400, message=err)
            return response(200, data=updated, message="Return rejected")

        # ── PUT /admin/returns/{id}/refund ────────────────────────────────────
        if path.startswith("/admin/returns/") and "/refund" in path and method == "PUT":
            return_id = path.split("/")[3]
            updated, err = process_refund_admin(return_id)
            if err:
                return response(400, message=err)
            return response(200, data=updated, message="Refund processed")

        return response(404, message="Route not found")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return response(500, message="Internal server error")
