import json
import uuid
import boto3
from utils import response


dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")
sts = boto3.client("sts")
orders_table = dynamodb.Table("orders_table_guru")

# Payment limits
MAX_PAYMENT_AMOUNT = 1_000_000   # 10,000.00 in currency units (price stored as cents)
MIN_PAYMENT_AMOUNT = 1           # At least 1 unit

# Simulated decline codes with realistic business rules
DECLINE_RULES = [
    {
        "code": "INSUFFICIENT_FUNDS",
        "message": "Payment declined: insufficient funds.",
        "condition": lambda amount, order: amount > 500_000  # > $5,000
    },
    {
        "code": "CARD_VELOCITY_EXCEEDED",
        "message": "Payment declined: too many recent transactions.",
        "condition": lambda amount, order: len(order.get("items", [])) > 10
    },
]


def fetch_order(order_id):
    try:
        result = orders_table.get_item(Key={"order_id": order_id})
        return result.get("Item")
    except Exception as e:
        print(f"ERROR fetching order: {str(e)}")
        return None


def calculate_total(items):
    return sum(float(item["price"]) * int(item["quantity"]) for item in items)


def update_order_status(order_id, status):
    try:
        orders_table.update_item(
            Key={"order_id": order_id},
            UpdateExpression="SET #s = :status",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":status": status}
        )
    except Exception as e:
        print(f"ERROR updating order status: {str(e)}")


def publish_payment_notification(order_id, payment_status, decline_code=None):
    try:
        account_id = sts.get_caller_identity()['Account']
        topic_arn = f"arn:aws:sns:ap-southeast-1:{account_id}:order-notifications-guru"

        subject = f"Payment {payment_status.title()}: Order {order_id}"
        message = f"Payment for order {order_id} has {payment_status}."
        if decline_code:
            message += f" Decline code: {decline_code}."

        sns.publish(TopicArn=topic_arn, Subject=subject, Message=message)
        print(f"INFO: Payment notification sent for order {order_id}")
    except Exception as e:
        print(f"ERROR publishing payment notification: {str(e)}")


def process_payment(order_id, amount, order):
    """
    Structured payment processor with business rule validation.
    Returns (success, payment_record, decline_code, message).
    """
    payment_id = str(uuid.uuid4())

    # Hard limits
    if amount < MIN_PAYMENT_AMOUNT:
        return False, None, "INVALID_AMOUNT", f"Amount must be at least {MIN_PAYMENT_AMOUNT}"
    if amount > MAX_PAYMENT_AMOUNT:
        return False, None, "AMOUNT_EXCEEDS_LIMIT", f"Amount exceeds maximum allowed ({MAX_PAYMENT_AMOUNT})"

    # Business rule decline checks
    for rule in DECLINE_RULES:
        if rule["condition"](amount, order):
            payment = {
                "payment_id": payment_id,
                "order_id": order_id,
                "amount": amount,
                "status": "declined",
                "decline_code": rule["code"]
            }
            return False, payment, rule["code"], rule["message"]

    # Payment approved
    payment = {
        "payment_id": payment_id,
        "order_id": order_id,
        "amount": amount,
        "status": "success",
        "decline_code": None
    }
    return True, payment, None, "Payment successful"


def lambda_handler(event, context):
    try:
        path = event.get("rawPath") or event.get("path", "")
        method = event.get("requestContext", {}).get("http", {}).get("method", "")

        # Strip /v1 prefix for backward compatibility
        if path.startswith("/v1/"):
            path = path[3:]

        print(f"INFO: Path={path}, Method={method}")

        # 🔹 POST /payment
        if path == "/payment" and method == "POST":
            body = json.loads(event.get("body") or "{}")

            order_id = body.get("order_id")
            amount   = body.get("amount")

            # Input validation
            if not order_id:
                return response(400, message="order_id is required")
            if amount is None:
                return response(400, message="amount is required")

            try:
                amount = float(amount)
            except (TypeError, ValueError):
                return response(400, message="amount must be a valid number")

            if amount <= 0:
                return response(400, message="amount must be greater than zero")

            # Fetch and validate order
            order = fetch_order(order_id)
            if not order:
                return response(400, message="Invalid order: order not found")

            if order.get("status") == "paid":
                return response(400, message="Order has already been paid")

            # Verify amount matches order total
            actual_total = calculate_total(order.get("items", []))
            if abs(amount - actual_total) > 0.01:
                return response(400, message=f"Amount mismatch: received {amount:.2f}, expected {actual_total:.2f}")

            # Run payment through processor
            success, payment, decline_code, message = process_payment(order_id, amount, order)

            if success:
                update_order_status(order_id, "paid")
                publish_payment_notification(order_id, "success")
                return response(200, data=payment, message=message)
            else:
                publish_payment_notification(order_id, "failed", decline_code)
                return response(400, data=payment, message=message)

        # 🔹 Invalid route
        return response(404, message="Route not found")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return response(500, message="Internal server error")