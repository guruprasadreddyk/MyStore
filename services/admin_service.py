import json
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Attr
from utils import convert_decimal, response

dynamodb       = boto3.resource("dynamodb")
products_table = dynamodb.Table("products_table_guru")
orders_table   = dynamodb.Table("orders_table_guru")
cart_table     = dynamodb.Table("cart_table_guru")


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
        orders_result = orders_table.scan()
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
        products_result = products_table.scan(
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

        return {
            "total_orders":   total_orders,
            "total_revenue":  round(total_revenue, 2),
            "status_counts":  status_counts,
            "low_stock":      low_stock,
            "top_products":   [{"product_id": pid, "units_sold": qty} for pid, qty in top_products]
        }
    except Exception as e:
        print(f"ERROR getting dashboard stats: {str(e)}")
        return {}


# ─── Product management ───────────────────────────────────────────────────────

def get_all_products_admin():
    """Full scan — no pagination limit, for admin view."""
    try:
        items = []
        result = products_table.scan()
        items.extend(result.get("Items", []))
        while result.get("LastEvaluatedKey"):
            result = products_table.scan(ExclusiveStartKey=result["LastEvaluatedKey"])
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

    update_expr   = "SET " + ", ".join(f"#{k} = :{k}" for k in filtered)
    expr_names    = {f"#{k}": k for k in filtered}
    expr_values   = {}
    for k, v in filtered.items():
        if k in ("price", "stock_quantity"):
            expr_values[f":{k}"] = int(v)
        else:
            expr_values[f":{k}"] = str(v)

    try:
        result = products_table.update_item(
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
        products_table.put_item(Item=item)
        return convert_decimal(item), None
    except Exception as e:
        print(f"ERROR adding product: {str(e)}")
        return None, str(e)


def delete_product(product_id):
    try:
        products_table.delete_item(Key={"id": str(product_id)})
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
        result = orders_table.scan(**kwargs)
        items.extend(result.get("Items", []))
        while result.get("LastEvaluatedKey"):
            kwargs["ExclusiveStartKey"] = result["LastEvaluatedKey"]
            result = orders_table.scan(**kwargs)
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
        result = orders_table.update_item(
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

        return response(404, message="Route not found")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return response(500, message="Internal server error")
