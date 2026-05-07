import json
import uuid
import boto3
from decimal import Decimal
from datetime import datetime
from botocore.exceptions import ClientError
from utils import convert_decimal, response, get_user_id, get_user_email, get_email_verified, send_email_via_resend, fetch_product, publish_sns_notification, get_table_name
from validation import validate

# Lazy-load tables for testability
def get_orders_table():
    return boto3.resource("dynamodb").Table(get_table_name("orders"))

def get_cart_table():
    return boto3.resource("dynamodb").Table(get_table_name("cart"))

def get_product_table():
    return boto3.resource("dynamodb").Table(get_table_name("products"))

def get_returns_table():
    return boto3.resource("dynamodb").Table(get_table_name("returns"))


def fetch_cart(user_id):
    try:
        result = get_cart_table().get_item(Key={"user_id": user_id})
        return convert_decimal(result.get("Item", {}).get("cart", []))
    except Exception as e:
        print("ERROR fetching cart:", str(e))
        return []


# 🔹 Aggregate duplicates → quantity
def aggregate_items(items):
    item_map = {}

    for item in items:
        item_id = str(item["id"])
        variant_id = item.get("variant_id")
        key = (item_id, variant_id)

        if key in item_map:
            item_map[key]["quantity"] += 1
        else:
            entry = {
                "id": item["id"],
                "name": item["name"],
                "price": item["price"],
                "quantity": 1
            }
            if variant_id:
                entry["variant_id"] = variant_id
            item_map[key] = entry

    return list(item_map.values())


def clear_cart(user_id):
    try:
        get_cart_table().put_item(Item={
            "user_id": user_id,
            "cart": []
        })
    except Exception as e:
        print("ERROR clearing cart:", str(e))


def save_order(order):
    try:
        get_orders_table().put_item(Item=order)
    except Exception as e:
        print(f"ERROR saving order: {str(e)}")


def reserve_inventory(items):
    """
    Atomically decrement stock for each item using conditional writes.
    Returns (success, failed_item_id) — rolls back already-decremented items on failure.
    """
    reserved = []
    for item in items:
        product_id = str(item["id"])
        quantity = item.get("quantity", 1)
        try:
            get_product_table().update_item(
                Key={"id": product_id},
                UpdateExpression="SET stock_quantity = stock_quantity - :qty",
                ConditionExpression="stock_quantity >= :qty",
                ExpressionAttributeValues={":qty": quantity}
            )
            reserved.append(item)
            print(f"INFO: Reserved {quantity} units of product {product_id}")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                print(f"ERROR: Insufficient stock for product {product_id}")
                # Roll back already-reserved items
                _rollback_inventory(reserved)
                return False, product_id
            print(f"ERROR: Unexpected error reserving product {product_id}: {str(e)}")
            _rollback_inventory(reserved)
            return False, product_id
    return True, None


def _rollback_inventory(reserved_items):
    """Restore stock for items that were already decremented before a failure."""
    for item in reserved_items:
        product_id = str(item["id"])
        quantity = item.get("quantity", 1)
        try:
            get_product_table().update_item(
                Key={"id": product_id},
                UpdateExpression="SET stock_quantity = stock_quantity + :qty",
                ExpressionAttributeValues={":qty": quantity}
            )
            print(f"INFO: Rolled back {quantity} units for product {product_id}")
        except Exception as e:
            print(f"ERROR: Failed to rollback inventory for {product_id}: {str(e)}")


def publish_order_notification(order):
    try:
        customer_email = order.get('user_email', '')
        name           = order.get('address', {}).get('full_name', 'there')
        city           = order.get('address', {}).get('city', '')
        grand_total    = int(order.get('grand_total', 0))
        order_ref      = order['order_id'][:8].upper()

        # SNS (admin notification)
        publish_sns_notification(
            subject=f"Order Confirmed: #{order_ref}",
            message=f"Order #{order_ref} placed by {name} ({customer_email}). Total: ₹{grand_total:,}"
        )

        # Resend (customer email)
        items_html = "".join(
            f"<tr><td style='padding:6px 0;border-bottom:1px solid #eee'>{i['name']}</td>"
            f"<td style='padding:6px 0;border-bottom:1px solid #eee;text-align:right'>×{int(i['quantity'])}</td>"
            f"<td style='padding:6px 0;border-bottom:1px solid #eee;text-align:right'>₹{int(i['price']) * int(i['quantity']):,}</td></tr>"
            for i in order.get('items', [])
        )
        subtotal        = int(order.get('subtotal', 0))
        delivery_charge = int(order.get('delivery_charge', 0))
        gst             = int(order.get('gst', 0))
        send_email_via_resend(
            to_email  = customer_email,
            subject   = f"Order Confirmed — #{order_ref} | MyStore",
            html_body = f"""<div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px;color:#333">
<h2 style="color:#10b981">🛒 Order Confirmed!</h2>
<p>Hi <strong>{name}</strong>, thank you for your order.</p>
<p>Order Reference: <strong>#{order_ref}</strong></p>
<table style="width:100%;border-collapse:collapse;margin:16px 0">
  <thead><tr style="border-bottom:2px solid #eee">
    <th style="text-align:left;padding:8px 0">Item</th>
    <th style="text-align:right;padding:8px 0">Qty</th>
    <th style="text-align:right;padding:8px 0">Amount</th>
  </tr></thead>
  <tbody>{items_html}</tbody>
  <tfoot>
    <tr><td colspan="2" style="padding:8px 0;border-top:1px solid #eee">Subtotal</td><td style="text-align:right;padding:8px 0;border-top:1px solid #eee">₹{subtotal:,}</td></tr>
    <tr><td colspan="2" style="padding:4px 0">Delivery</td><td style="text-align:right;padding:4px 0">{'FREE' if delivery_charge == 0 else f'₹{delivery_charge:,}'}</td></tr>
    <tr><td colspan="2" style="padding:4px 0">GST (18%)</td><td style="text-align:right;padding:4px 0">₹{gst:,}</td></tr>
    <tr style="font-weight:bold"><td colspan="2" style="padding:8px 0;border-top:2px solid #eee">Grand Total</td><td style="text-align:right;padding:8px 0;border-top:2px solid #eee">₹{grand_total:,}</td></tr>
  </tfoot>
</table>
<p>Delivering to <strong>{city}</strong>. Please complete payment to confirm your order.</p>
<hr style="border:none;border-top:1px solid #eee;margin:24px 0"/>
<p style="font-size:0.8rem;color:#999">MyStore · This is an automated email.</p>
</div>""",
            text_body = f"Hi {name}, your order #{order_ref} is confirmed. Total: ₹{grand_total:,}. Please pay to confirm."
        )
    except Exception as e:
        # Notification failure must never crash the order handler — order is already saved
        print(f"WARN: Failed to send order notification for {order.get('order_id', 'unknown')}: {str(e)}")


# ── Return Management ─────────────────────────────────────────────────────────

def create_return_request(order_id, user_id, reason):
    """Create a return request for a delivered order."""
    try:
        order = get_order_by_id(order_id)
        if not order:
            return None, "Order not found"
        
        if order.get("user_id") != user_id:
            return None, "Not authorized to return this order"
        
        if order.get("status") != "delivered":
            return None, f"Can only return delivered orders. Current status: {order.get('status')}"
        
        return_request = {
            "return_id": str(uuid.uuid4()),
            "order_id": order_id,
            "user_id": user_id,
            "reason": reason,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "refund_amount": int(order.get("grand_total", 0)),
            "refund_status": "pending"
        }
        
        # Store return request in a returns table
        get_returns_table().put_item(Item=return_request)
        
        # Update order status to show return is pending
        order["status"] = "return_pending"
        order["return_id"] = return_request["return_id"]
        save_order(order)
        
        # Notify customer
        send_email_via_resend(
            to_email=order.get("user_email", ""),
            subject=f"Return Request Received — #{order_id[:8].upper()} | MyStore",
            html_body=f"""<div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
<h2 style="color:#3b82f6">📦 Return Request Received</h2>
<p>Hi {order.get('address', {}).get('full_name', 'there')},</p>
<p>We've received your return request for order <strong>#{order_id[:8].upper()}</strong>.</p>
<p><strong>Reason:</strong> {reason}</p>
<p><strong>Refund Amount:</strong> ₹{return_request['refund_amount']:,}</p>
<p>We'll review your request and send you a return label within 24 hours.</p>
<hr style="border:none;border-top:1px solid #eee;margin:24px 0"/>
<p style="font-size:0.8rem;color:#999">MyStore · This is an automated email.</p>
</div>""",
            text_body=f"Return request received for order #{order_id[:8].upper()}. Reason: {reason}. Refund amount: ₹{return_request['refund_amount']:,}"
        )
        
        return return_request, None
    except Exception as e:
        print(f"ERROR creating return request: {str(e)}")
        return None, str(e)


def approve_return(return_id, user_id):
    """Approve a return request (admin action proxied through order service)."""
    try:
        result = get_returns_table().get_item(Key={"return_id": return_id})
        return_req = result.get("Item")
        
        if not return_req:
            return None, "Return request not found"
        
        return_req["status"] = "approved"
        return_req["approved_at"] = datetime.utcnow().isoformat() + "Z"
        get_returns_table().put_item(Item=return_req)
        
        # Fetch order to get customer email
        order = get_order_by_id(return_req.get("order_id", ""))
        customer_email = order.get("user_email", "") if order else ""

        # Send approval email
        send_email_via_resend(
            to_email=customer_email,
            subject=f"Return Approved — #{return_id[:8].upper()} | MyStore",
            html_body=f"""<div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
<h2 style="color:#10b981">✅ Return Approved</h2>
<p>Your return request has been approved.</p>
<p>Please ship the item back to us using the return label.</p>
<p>Once we receive and inspect the item, we'll process your refund of ₹{return_req['refund_amount']:,}.</p>
</div>""",
            text_body=f"Your return has been approved. Refund amount: ₹{return_req['refund_amount']:,}"
        )
        
        return return_req, None
    except Exception as e:
        print(f"ERROR approving return: {str(e)}")
        return None, str(e)


def process_refund(return_id, user_id):
    """Process refund for an approved return."""
    try:
        result = get_returns_table().get_item(Key={"return_id": return_id})
        return_req = result.get("Item")
        
        if not return_req:
            return None, "Return request not found"
        
        if return_req.get("status") != "approved":
            return None, "Return must be approved before refunding"
        
        # In production, call Razorpay refund API here
        # For now, just mark as refunded
        return_req["status"] = "refunded"
        return_req["refund_status"] = "completed"
        return_req["refunded_at"] = datetime.utcnow().isoformat() + "Z"
        get_returns_table().put_item(Item=return_req)
        
        # Update order status
        order = get_order_by_id(return_req["order_id"])
        if order:
            order["status"] = "refunded"
            save_order(order)
        
        # Send refund email
        customer_email = order.get("user_email", "") if order else ""
        send_email_via_resend(
            to_email=customer_email,
            subject=f"Refund Processed — #{return_id[:8].upper()} | MyStore",
            html_body=f"""<div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
<h2 style="color:#10b981">💰 Refund Processed</h2>
<p>Your refund of ₹{return_req['refund_amount']:,} has been processed.</p>
<p>The amount will appear in your account within 5-7 business days.</p>
</div>""",
            text_body=f"Refund of ₹{return_req['refund_amount']:,} has been processed. It will appear in your account within 5-7 business days."
        )
        
        return return_req, None
    except Exception as e:
        print(f"ERROR processing refund: {str(e)}")
        return None, str(e)


def get_order_by_id(order_id):
    try:
        result = get_orders_table().get_item(Key={"order_id": order_id})
        item = result.get("Item")
        return convert_decimal(item) if item else None
    except Exception as e:
        print(f"ERROR loading order: {str(e)}")
        return None


def get_all_orders(user_id):
    """Query orders by user_id using the GSI — no full table scan."""
    try:
        from boto3.dynamodb.conditions import Key
        result = get_orders_table().query(
            IndexName="user_id-index",
            KeyConditionExpression=Key("user_id").eq(user_id)
        )
        return convert_decimal(result.get("Items", []))
    except Exception as e:
        print(f"ERROR loading orders: {str(e)}")
        return []


def lambda_handler(event, context):
    try:
        user_id    = get_user_id(event)
        user_email = get_user_email(event)
        email_verified = get_email_verified(event)
        path = event.get("rawPath") or event.get("path", "")
        method = event.get("requestContext", {}).get("http", {}).get("method", "")

        # Strip /v1 prefix for backward compatibility
        if path.startswith("/v1/"):
            path = path[3:]  # Remove "/v1" prefix

        print(f"INFO: Path={path}, Method={method}, User={user_id}")

        # 🔹 GET /order → list all orders (for order history)
        if path == "/order" and method == "GET":
            orders = get_all_orders(user_id)
            return response(200, data=orders)

        # 🔹 POST /order
        if path == "/order" and method == "POST":
            body  = json.loads(event.get("body") or "{}")
            items = body.get("items", [])

            # Validate input
            try:
                validate(body, "create_order")
            except ValueError as e:
                return response(400, message=str(e))

            # ── Address validation ────────────────────────────────────────────
            address = body.get("address", {})
            required_address_fields = ["full_name", "phone", "address_line1", "city", "state", "pincode"]
            missing = [f for f in required_address_fields if not address.get(f, "").strip()]
            if missing:
                return response(400, message=f"Missing address fields: {', '.join(missing)}")

            # ── Items validation ──────────────────────────────────────────────
            if not items or not isinstance(items, list):
                return response(400, message="Items list is required")
            
            cart_items = fetch_cart(user_id)

            if not cart_items:
                return response(400, message="Cart is empty")

            # build cart lookup (id → quantity)
            cart_map = {
                str(item["id"]): item.get("quantity", 1)
                for item in cart_items
            }

            request_count = {}
            validated_items = []

            for item in items:
                allowed_keys = {"id", "variant_id"}
                if not set(item.keys()).issubset(allowed_keys):
                    return response(400, message=f"Each item must contain only 'id' and optionally 'variant_id'")

                product_id = str(item.get("id"))
                variant_id = item.get("variant_id")

                if not product_id:
                    return response(400, message="Invalid product id")
                
                # count requested items
                request_count[product_id] = request_count.get(product_id, 0) + 1

                # check if exists in cart
                if product_id not in cart_map:
                    return response(400, message=f"Item {product_id} not in cart")

                # check quantity limit
                if request_count[product_id] > cart_map[product_id]:
                    return response(400, message=f"Requested quantity exceeds cart for item {product_id}")

                product = fetch_product(product_id)

                if not product:
                    return response(400, message=f"Invalid product id: {product_id}")

                # If variant_id provided, get variant price; otherwise use product price
                if variant_id:
                    variants = product.get("variants", [])
                    variant = next((v for v in variants if v.get("variant_id") == variant_id), None)
                    if not variant:
                        return response(400, message=f"Invalid variant: {variant_id}")
                    item_price = variant.get("price", product["price"])
                else:
                    item_price = product["price"]

                validated_item = {
                    "id": product["id"],
                    "name": product["name"],
                    "price": int(item_price)
                }
                if variant_id:
                    validated_item["variant_id"] = variant_id
                
                validated_items.append(validated_item)

            # ✅ aggregate duplicates → quantity
            processed_items = aggregate_items(validated_items)

            # ✅ Reserve inventory atomically before saving the order
            success, failed_product_id = reserve_inventory(processed_items)
            if not success:
                return response(400, message=f"Insufficient stock for product {failed_product_id}")

            # ── Pricing breakdown ─────────────────────────────────────────────
            subtotal         = int(sum(int(i["price"]) * int(i["quantity"]) for i in processed_items))
            delivery_charge  = 0 if subtotal >= 500 else 49
            gst              = round(subtotal * 0.18)
            grand_total      = subtotal + delivery_charge + gst

            order = {
                "order_id":       str(uuid.uuid4()),
                "user_id":        user_id,
                "user_email":     user_email,
                "email_verified": email_verified,
                "items":          processed_items,
                "address":        address,
                "subtotal":       subtotal,
                "delivery_charge":delivery_charge,
                "gst":            gst,
                "grand_total":    grand_total,
                "status":         "created",
                "created_at":     datetime.utcnow().isoformat() + "Z"
            }

            if not user_email:
                print(f"WARN: Order created for user {user_id} with no email — transactional emails will not be sent. "
                      "Ensure the Auth0 API has 'openid profile email' scopes and the JWT includes the email claim.")
            elif not email_verified:
                print(f"WARN: Order created for user {user_id} with unverified email {user_email} — skipping confirmation email.")

            save_order(order)
            clear_cart(user_id)

            if email_verified:
                publish_order_notification(order)

            # SQS fulfillment is triggered by payment_service after payment succeeds,
            # not here — ensures shipped status only follows confirmed payment.

            return response(200, data=order, message="Order created successfully")

        # 🔹 GET /order/{id}
        if path.startswith("/order/") and method == "GET":
            order_id = path.split("/")[-1]

            if not order_id:
                return response(400, message="Order ID required")

            order = get_order_by_id(order_id)

            if not order:
                return response(404, message="Order not found")

            return response(200, data=order)

        # 🔹 PUT /order/{id} → update status
        if path.startswith("/order/") and method == "PUT":
            order_id = path.split("/")[-1]
            body = json.loads(event.get("body") or "{}")

            order = get_order_by_id(order_id)

            if not order:
                return response(404, message="Order not found")

            order["status"] = body.get("status", order["status"])
            save_order(order)

            return response(200, data=order, message="Order updated")

        # 🔹 DELETE /order/{id} → cancel order
        if path.startswith("/order/") and method == "DELETE":
            order_id = path.split("/")[-1]

            order = get_order_by_id(order_id)

            if not order:
                return response(404, message="Order not found")

            # Only the order owner can cancel
            if order.get("user_id") != user_id:
                return response(403, message="Not authorised to cancel this order")

            # Only cancellable before payment
            cancellable = {"created"}
            if order.get("status") not in cancellable:
                return response(400, message=f"Cannot cancel an order with status '{order.get('status')}'. Only orders in 'created' state can be cancelled.")

            # Restore inventory for each item
            _rollback_inventory(order.get("items", []))

            order["status"] = "cancelled"
            save_order(order)

            return response(200, data=order, message="Order cancelled and inventory restored")

        # 🔹 POST /return → create return request
        if path == "/return" and method == "POST":
            body = json.loads(event.get("body") or "{}")
            
            # Validate input
            try:
                validate(body, "create_return")
            except ValueError as e:
                return response(400, message=str(e))
            
            order_id = body.get("order_id")
            reason = body.get("reason", "")

            return_req, error = create_return_request(order_id, user_id, reason)
            if error:
                return response(400, message=error)

            return response(200, data=return_req, message="Return request created")

        # 🔹 GET /return/{id} → get return request
        if path.startswith("/return/") and method == "GET":
            return_id = path.split("/")[-1]
            try:
                result = get_returns_table().get_item(Key={"return_id": return_id})
                return_req = result.get("Item")
                
                if not return_req:
                    return response(404, message="Return request not found")
                
                if return_req.get("user_id") != user_id:
                    return response(403, message="Not authorized")
                
                return response(200, data=convert_decimal(return_req))
            except Exception as e:
                print(f"ERROR getting return: {str(e)}")
                return response(500, message="Internal server error")

        # 🔹 Invalid route
        return response(404, message="Route not found")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return response(500, message="Internal server error")
