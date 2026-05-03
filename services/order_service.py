import json
import os
import uuid
import boto3
from decimal import Decimal
from botocore.exceptions import ClientError
from utils import convert_decimal, response, get_user_id, get_user_email


dynamodb = boto3.resource("dynamodb")
sqs = boto3.client("sqs")
sns = boto3.client("sns")
sts = boto3.client("sts")
orders_table  = dynamodb.Table("orders_table_guru")
product_table = dynamodb.Table("products_table_guru")
cart_table    = dynamodb.Table("cart_table_guru")
cart_table = dynamodb.Table("cart_table_guru")





# 🔹 Fetch product from DynamoDB
def fetch_product(product_id):
    try:
        result = product_table.get_item(Key={"id": str(product_id)})
        item = result.get("Item")
        return convert_decimal(item) if item else None
    except Exception as e:
        print("ERROR fetching product:", str(e))
        return None


def fetch_cart(user_id):
    try:
        result = cart_table.get_item(Key={"user_id": user_id})
        return convert_decimal(result.get("Item", {}).get("cart", []))
    except Exception as e:
        print("ERROR fetching cart:", str(e))
        return []


# 🔹 Aggregate duplicates → quantity
def aggregate_items(items):
    item_map = {}

    for item in items:
        item_id = str(item["id"])

        if item_id in item_map:
            item_map[item_id]["quantity"] += 1
        else:
            item_map[item_id] = {
                "id": item["id"],
                "name": item["name"],
                "price": item["price"],
                "quantity": 1
            }

    return list(item_map.values())


def clear_cart(user_id):
    try:
        cart_table.put_item(Item={
            "user_id": user_id,
            "cart": []
        })
    except Exception as e:
        print("ERROR clearing cart:", str(e))


def save_order(order):
    try:
        orders_table.put_item(Item=order)
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
            product_table.update_item(
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
            product_table.update_item(
                Key={"id": product_id},
                UpdateExpression="SET stock_quantity = stock_quantity + :qty",
                ExpressionAttributeValues={":qty": quantity}
            )
            print(f"INFO: Rolled back {quantity} units for product {product_id}")
        except Exception as e:
            print(f"ERROR: Failed to rollback inventory for {product_id}: {str(e)}")


def send_order_to_queue(order):
    try:
        queue_name = os.environ.get('SQS_QUEUE_NAME', 'order-processing-queue-guru')
        response = sqs.get_queue_url(QueueName=queue_name)
        queue_url = response['QueueUrl']
        
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(order)
        )
        print(f"INFO: Order {order['order_id']} sent to SQS")
    except Exception as e:
        print(f"ERROR sending to SQS: {str(e)}")


def publish_order_notification(order):
    try:
        account_id = sts.get_caller_identity()['Account']
        region     = os.environ.get("AWS_REGION_NAME", "ap-southeast-1")
        topic_name = os.environ.get("SNS_TOPIC_NAME", "order-notifications-guru")
        topic_arn  = f"arn:aws:sns:{region}:{account_id}:{topic_name}"

        subject = f"Order Confirmed: #{order['order_id'][:8].upper()}"
        message = (
            f"Hi {order.get('address', {}).get('full_name', 'there')},\n\n"
            f"Your order #{order['order_id'][:8].upper()} has been placed successfully.\n"
            f"Items: {len(order['items'])}\n"
            f"Grand Total: ₹{order.get('grand_total', 0):,}\n"
            f"Delivery to: {order.get('address', {}).get('city', '')}, "
            f"{order.get('address', {}).get('state', '')}\n"
            f"Customer: {order.get('user_email', '')}"
        )

        sns.publish(TopicArn=topic_arn, Subject=subject, Message=message)
        print(f"INFO: Order notification sent for {order['order_id']}")
    except Exception as e:
        print(f"ERROR publishing to SNS: {str(e)}")


def get_order_by_id(order_id):
    try:
        result = orders_table.get_item(Key={"order_id": order_id})
        item = result.get("Item")
        return convert_decimal(item) if item else None
    except Exception as e:
        print(f"ERROR loading order: {str(e)}")
        return None


def get_all_orders(user_id):
    try:
        result = orders_table.scan()
        items = result.get("Items", [])
        user_items = [item for item in items if item.get("user_id") == user_id]
        return convert_decimal(user_items)
    except Exception as e:
        print(f"ERROR loading orders: {str(e)}")
        return []


def lambda_handler(event, context):
    try:
        user_id    = get_user_id(event)
        user_email = get_user_email(event)
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

            # ── Address validation ────────────────────────────────────────────
            address = body.get("address", {})
            required_address_fields = ["full_name", "phone", "address_line1", "city", "state", "pincode"]
            missing = [f for f in required_address_fields if not address.get(f, "").strip()]
            if missing:
                return response(400, message=f"Missing address fields: {', '.join(missing)}")

            # Basic phone validation
            phone = address["phone"].strip()
            if not phone.isdigit() or len(phone) != 10:
                return response(400, message="Phone must be a 10-digit number")

            # Basic PIN code validation
            pincode = address["pincode"].strip()
            if not pincode.isdigit() or len(pincode) != 6:
                return response(400, message="PIN code must be a 6-digit number")

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
                if set(item.keys()) != {"id"}:
                    return response(400, message="Each item must contain only 'id'")

                product_id = str(item.get("id"))

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

                validated_items.append({
                    "id": product["id"],
                    "name": product["name"],
                    "price": product["price"]
                })

            # ✅ aggregate duplicates → quantity
            processed_items = aggregate_items(validated_items)

            # ✅ Reserve inventory atomically before saving the order
            success, failed_product_id = reserve_inventory(processed_items)
            if not success:
                return response(400, message=f"Insufficient stock for product {failed_product_id}")

            # ── Pricing breakdown ─────────────────────────────────────────────
            subtotal         = sum(i["price"] * i["quantity"] for i in processed_items)
            delivery_charge  = 0 if subtotal >= 500 else 49
            gst              = round(subtotal * 0.18)
            grand_total      = subtotal + delivery_charge + gst

            order = {
                "order_id":       str(uuid.uuid4()),
                "user_id":        user_id,
                "user_email":     user_email,
                "items":          processed_items,
                "address":        address,
                "subtotal":       subtotal,
                "delivery_charge":delivery_charge,
                "gst":            gst,
                "grand_total":    grand_total,
                "status":         "created"
            }

            save_order(order)
            clear_cart(user_id)

            # Notify SNS that order was created (informational only)
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

        # 🔹 Invalid route
        return response(404, message="Route not found")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return response(500, message="Internal server error")