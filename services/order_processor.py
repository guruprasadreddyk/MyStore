import json
import boto3
import os
from utils import convert_decimal

# Clients
dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")
sts = boto3.client("sts")

orders_table = dynamodb.Table("orders_table_guru")
products_table = dynamodb.Table("products_table_guru")

def update_inventory(items):
    for item in items:
        product_id = item.get("id")
        quantity = item.get("quantity", 1)
        
        try:
            products_table.update_item(
                Key={"id": str(product_id)},
                UpdateExpression="SET stock_quantity = stock_quantity - :val",
                ConditionExpression="stock_quantity >= :val",
                ExpressionAttributeValues={":val": quantity}
            )
            print(f"INFO: Deducted {quantity} from product {product_id}")
        except Exception as e:
            print(f"ERROR: Failed to update inventory for {product_id}: {str(e)}")
            # Real systems would likely throw an error to dead-letter the SQS message here.

def publish_shipping_notification(order):
    try:
        account_id = sts.get_caller_identity()['Account']
        topic_arn = f"arn:aws:sns:ap-southeast-1:{account_id}:order-notifications-guru"
        
        subject = f"Order Shipped: {order['order_id']}"
        message = f"Great news! Your order {order['order_id']} has been fulfilled and shipped."
        
        sns.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
        print(f"INFO: Shipping notification sent for order {order['order_id']}")
    except Exception as e:
        print(f"ERROR publishing to SNS: {str(e)}")

def lambda_handler(event, context):
    try:
        # Process each SQS message
        for record in event['Records']:
            message_body = json.loads(record['body'])
            order_id = message_body.get('order_id')
            
            if order_id:
                # 1. Load the order
                order = orders_table.get_item(Key={"order_id": order_id}).get("Item")
                if order:
                    print(f"INFO: Processing order {order_id}")
                    
                    # 2. Update Inventory
                    items = order.get("items", [])
                    update_inventory(items)

                    # 3. Update order status to 'shipped'
                    order['status'] = 'shipped'
                    orders_table.put_item(Item=order)
                    print(f"INFO: Order {order_id} status updated to shipped")
                    
                    # 4. Send email/SNS notification
                    publish_shipping_notification(order)
                    
                else:
                    print(f"ERROR: Order {order_id} not found")
            else:
                print("ERROR: No order_id in message")
                
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