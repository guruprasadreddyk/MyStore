import json
import boto3
from decimal import Decimal

# Clients
dynamodb = boto3.resource("dynamodb")
orders_table = dynamodb.Table("orders_table_guru")

def convert_decimal(obj):
    if isinstance(obj, list):
        return [convert_decimal(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj)
    return obj

def lambda_handler(event, context):
    try:
        # Process each SQS message
        for record in event['Records']:
            message_body = json.loads(record['body'])
            order_id = message_body.get('order_id')
            
            if order_id:
                # Update order status to 'processing'
                order = orders_table.get_item(Key={"order_id": order_id}).get("Item")
                if order:
                    order['status'] = 'processing'
                    orders_table.put_item(Item=order)
                    print(f"INFO: Order {order_id} status updated to processing")
                    
                    # Here you could add more processing logic:
                    # - Send email notifications
                    # - Update inventory
                    # - Trigger shipping workflows
                    # - etc.
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