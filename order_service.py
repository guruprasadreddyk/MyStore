import json
import os
import uuid
import boto3
from decimal import Decimal


dynamodb = boto3.resource("dynamodb")
sqs = boto3.client("sqs")
sns = boto3.client("sns")
sts = boto3.client("sts")
orders_table = dynamodb.Table("orders_table_guru")
product_table = dynamodb.Table("products_table_guru")
cart_table = dynamodb.Table("cart_table_guru")


def convert_decimal(obj):
    if isinstance(obj, list):
        return [convert_decimal(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj)
    return obj


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


# 🔹 Fetch product from DynamoDB
def fetch_product(product_id):
    try:
        result = product_table.get_item(Key={"id": str(product_id)})
        item = result.get("Item")
        return convert_decimal(item) if item else None
    except Exception as e:
        print("ERROR fetching product:", str(e))
        return None


def fetch_cart():
    try:
        result = cart_table.get_item(Key={"user_id": "user1"})
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


def clear_cart():
    try:
        cart_table.put_item(Item={
            "user_id": "user1",
            "cart": []
        })
    except Exception as e:
        print("ERROR clearing cart:", str(e))


def save_order(order):
    try:
        orders_table.put_item(Item=order)
    except Exception as e:
        print(f"ERROR saving order: {str(e)}")


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
        topic_arn = f"arn:aws:sns:ap-southeast-1:{account_id}:order-notifications-guru"
        
        subject = f"New Order Created: {order['order_id']}"
        message = f"Order {order['order_id']} has been created with {len(order['items'])} items."
        
        sns.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
        print(f"INFO: Notification sent for order {order['order_id']}")
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


def get_all_orders():
    try:
        result = orders_table.scan()
        items = result.get("Items", [])
        return convert_decimal(items)
    except Exception as e:
        print(f"ERROR loading orders: {str(e)}")
        return []


def lambda_handler(event, context):
    try:
        path = event.get("rawPath") or event.get("path", "")
        method = event.get("requestContext", {}).get("http", {}).get("method", "")

        # Strip /v1 prefix for backward compatibility
        if path.startswith("/v1/"):
            path = path[3:]  # Remove "/v1" prefix

        print(f"INFO: Path={path}, Method={method}")

        # 🔹 GET /order → list all orders (for order history)
        if path == "/order" and method == "GET":
            orders = get_all_orders()
            return response(200, data=orders)

        # 🔹 POST /order
        if path == "/order" and method == "POST":
            body = json.loads(event.get("body") or "{}")
            items = body.get("items", [])

            # ✅ validation
            if not items or not isinstance(items, list):
                return response(400, message="Items list is required")
            
            cart_items = fetch_cart()

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

            order = {
                "order_id": str(uuid.uuid4()),
                "items": processed_items,
                "status": "created"
            }

            save_order(order)
            clear_cart()

            # Send order to SQS for processing
            send_order_to_queue(order)
            
            # Publish notification to SNS
            publish_order_notification(order)

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

        # 🔹 Invalid route
        return response(404, message="Route not found")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return response(500, message="Internal server error")