import json
import random
import uuid
import boto3


dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")
sts = boto3.client("sts")
orders_table = dynamodb.Table("orders_table_guru")


def fetch_order(order_id):
    try:
        result = orders_table.get_item(Key={"order_id": order_id})
        item = result.get("Item")
        return item
    except Exception as e:
        print(f"ERROR fetching order: {str(e)}")
        return None

def calculate_total(items):
    return sum(item["price"] * item["quantity"] for item in items)

# 🔹 Helper: Standard response
def response(status_code, data=None, message=None):
    body = {
        "status": "success" if status_code < 400 else "error",
        "data": data,
        "message": message
    }
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT,DELETE"
        },
        "body": json.dumps(body)
    }

def update_order_status(order_id):
    try:
        orders_table.update_item(
            Key={"order_id": order_id},
            UpdateExpression="SET #s = :status",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":status": "paid"}
        )
    except Exception as e:
        print(f"ERROR updating order status: {str(e)}")


def publish_payment_notification(order_id, payment_status):
    try:
        account_id = sts.get_caller_identity()['Account']
        topic_arn = f"arn:aws:sns:ap-southeast-1:{account_id}:order-notifications-guru"
        
        subject = f"Payment {payment_status.title()}: Order {order_id}"
        message = f"Payment for order {order_id} has {payment_status}."
        
        sns.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
        print(f"INFO: Payment notification sent for order {order_id}")
    except Exception as e:
        print(f"ERROR publishing payment notification: {str(e)}")


def lambda_handler(event, context):
    try:
        path = event.get("rawPath") or event.get("path", "")
        method = event.get("requestContext", {}).get("http", {}).get("method", "")

        print(f"INFO: Path={path}, Method={method}")

        # 🔹 POST /payment
        if path == "/payment" and method == "POST":
            body = json.loads(event.get("body") or "{}")

            order_id = body.get("order_id")
            amount = body.get("amount")

            print(f"DEBUG: Received order_id={order_id}, amount={amount}, type(amount)={type(amount)}")

            # validation
            if not order_id:
                return response(400, message="order_id is required")

            if not amount or amount <= 0:
                return response(400, message="Valid amount is required")

            order = fetch_order(order_id)
            print(f"DEBUG: Fetched order={order}")

            if not order:
                return response(400, message="Invalid order")

            actual_amount = calculate_total(order["items"])
            print(f"DEBUG: Calculated actual_amount={actual_amount}, type(actual_amount)={type(actual_amount)}")

            # Convert amount to float for comparison
            amount = float(amount)
            actual_amount = float(actual_amount)

            print(f"DEBUG: Comparing amount={amount} with actual_amount={actual_amount}")

            if abs(amount - actual_amount) > 0.01:  # Allow small floating point differences
                return response(400, message=f"Amount mismatch: received {amount}, expected {actual_amount}")

            # simulate payment
            payment_success = random.choice([True, False])

            payment = {
                "payment_id": str(uuid.uuid4()),
                "order_id": order_id,
                "amount": amount,
                "status": "success" if payment_success else "failed"
            }

            if payment_success:
                update_order_status(order_id)
                publish_payment_notification(order_id, "success")
                return response(200, data=payment, message="Payment successful")
            else:
                publish_payment_notification(order_id, "failed")
                return response(400, data=payment, message="Payment failed")

        # 🔹 Invalid route
        return response(404, message="Route not found")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return response(500, message="Internal server error")