import json
import boto3
import os
from utils import convert_decimal, send_email_via_resend, publish_sns_notification

# Lazy-load tables for testability
def get_orders_table():
    return boto3.resource("dynamodb").Table("orders_table_guru")


def publish_shipping_notification(order):
    customer_email = order.get('user_email', '')
    name           = order.get('address', {}).get('full_name', 'there')
    city           = order.get('address', {}).get('city', '')
    order_ref      = order['order_id'][:8].upper()

    # SNS (admin)
    publish_sns_notification(
        subject=f"Order Shipped: #{order_ref}",
        message=f"Order #{order_ref} shipped to {name} ({customer_email}) in {city}."
    )

    # Resend (customer)
    send_email_via_resend(
        to_email  = customer_email,
        subject   = f"Your Order Has Shipped — #{order_ref} | MyStore",
        html_body = f"""<div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
<h2 style="color:#06b6d4">🚚 Your Order Has Shipped!</h2>
<p>Hi <strong>{name}</strong>, great news!</p>
<p>Your order <strong>#{order_ref}</strong> has been dispatched and is on its way to <strong>{city}</strong>.</p>
<p>Estimated delivery: <strong>3–5 business days</strong>.</p>
<hr style="border:none;border-top:1px solid #eee;margin:24px 0"/>
<p style="font-size:0.8rem;color:#999">MyStore · This is an automated email.</p>
</div>""",
        text_body = f"Hi {name}, your order #{order_ref} has shipped! Estimated delivery to {city} in 3-5 business days."
    )


def lambda_handler(event, context):
    try:
        # Process each SQS message
        for record in event.get('Records', []):
            try:
                message_body = json.loads(record['body'])
            except (json.JSONDecodeError, KeyError):
                print("ERROR: Invalid JSON in SQS message")
                continue

            order_id = message_body.get('order_id')

            if not order_id:
                print("ERROR: No order_id in message")
                continue

            # Load the order
            order = get_orders_table().get_item(Key={"order_id": order_id}).get("Item")
            if not order:
                print(f"ERROR: Order {order_id} not found")
                continue

            print(f"INFO: Processing order {order_id}")

            # Update order status to 'shipped'
            order['status'] = 'shipped'
            get_orders_table().put_item(Item=order)
            print(f"INFO: Order {order_id} status updated to shipped")

            # Send shipping notification (non-fatal if it fails)
            try:
                publish_shipping_notification(order)
            except Exception as e:
                print(f"ERROR sending shipping notification for {order_id}: {str(e)}")

        return {
            'statusCode': 200,
            'body': json.dumps('Order processing completed')
        }

    except Exception as e:
        print(f"ERROR in order processor: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error processing orders')
        }
