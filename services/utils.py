import json
import os
import urllib.request
import boto3
from decimal import Decimal


# 🔹 Update order status (shared across services)
def update_order_status(order_id, new_status):
    """Update order status in orders table."""
    try:
        dynamodb = boto3.resource("dynamodb")
        orders_table = dynamodb.Table("orders_table_guru")
        
        orders_table.update_item(
            Key={"order_id": str(order_id)},
            UpdateExpression="SET #s = :status",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":status": new_status}
        )
        print(f"INFO: Order {order_id} status updated to {new_status}")
        return True
    except Exception as e:
        print(f"ERROR updating order status: {str(e)}")
        return False


# 🔹 Publish SNS notification (shared across services)
def publish_sns_notification(subject, message):
    """Publish notification to SNS topic."""
    try:
        sns = boto3.client("sns")
        sts = boto3.client("sts")
        
        account_id = sts.get_caller_identity()['Account']
        region     = os.environ.get("AWS_REGION_NAME", "ap-southeast-1")
        topic_name = os.environ.get("SNS_TOPIC_NAME", "order-notifications-guru")
        topic_arn  = f"arn:aws:sns:{region}:{account_id}:{topic_name}"
        
        sns.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
        print(f"INFO: SNS notification sent: {subject}")
        return True
    except Exception as e:
        print(f"ERROR publishing to SNS: {str(e)}")
        return False


# 🔹 Send email via Resend API with retry logic
def send_email_via_resend(to_email, subject, html_body, text_body=""):
    """Send transactional email via Resend API with exponential backoff retry. Non-fatal — logs error if it fails."""
    # Read env vars at call time, not module import time — Lambda may not have
    # injected them yet when the module is first loaded during a cold start.
    resend_api_key = os.environ.get("RESEND_API_KEY", "")
    resend_from    = os.environ.get("RESEND_FROM", "MyStore <onboarding@resend.dev>")

    if not resend_api_key:
        # No API key — log the email content so it's visible in Lambda logs during testing
        print(f"INFO: RESEND_API_KEY not configured — email not sent.")
        print(f"  TO:      {to_email}")
        print(f"  SUBJECT: {subject}")
        print(f"  BODY:    {text_body or '(html only)'}")
        return
    if not to_email:
        print("INFO: No recipient email address — skipping email send")
        return

    max_retries = 3
    for attempt in range(max_retries):
        try:
            payload = json.dumps({
                "from":    resend_from,
                "to":      [to_email],
                "subject": subject,
                "html":    html_body,
                "text":    text_body
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://api.resend.com/emails",
                data    = payload,
                headers = {
                    "Content-Type":  "application/json",
                    "Authorization": f"Bearer {resend_api_key}"
                },
                method = "POST"
            )
            with urllib.request.urlopen(req, timeout=10) as res:
                result = json.loads(res.read())
                print(f"INFO: Email sent via Resend — id: {result.get('id')}")
                return  # Success, exit
        except Exception as e:
            print(f"ERROR sending email via Resend (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                import time
                time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
            else:
                print(f"ERROR: Failed to send email after {max_retries} attempts")


# 🔹 Fetch product from DynamoDB
def fetch_product(product_id):
    """Fetch a single product by ID from DynamoDB."""
    try:
        product_table = boto3.resource("dynamodb").Table("products_table_guru")
        result = product_table.get_item(Key={"id": str(product_id)})
        item   = result.get("Item")
        return convert_decimal(item) if item else None
    except Exception as e:
        print(f"ERROR fetching product: {str(e)}")
        return None


# 🔹 Convert Decimal to int/float for JSON response
def convert_decimal(obj):
    if isinstance(obj, list):
        return [convert_decimal(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        # Convert to float to handle both ints and floats gracefully
        val = float(obj)
        # If it's a whole number, return as int for cleaner JSON
        return int(val) if val.is_integer() else val
    return obj


# 🔹 Standard API response
def response(status_code, data=None, message=None):
    body = {
        "status": "success" if status_code < 400 else "error"
    }
    
    if data is not None:
        body["data"] = convert_decimal(data)
    else:
        body["data"] = None
        
    if message is not None:
        body["message"] = message
    else:
        body["message"] = None

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


# 🔹 Extract user ID from Auth0 JWT Authorizer
def get_user_id(event):
    try:
        return event['requestContext']['authorizer']['jwt']['claims']['sub']
    except KeyError:
        return None


# 🔹 Extract user email from Auth0 JWT Authorizer
def get_user_email(event):
    try:
        claims = event['requestContext']['authorizer']['jwt']['claims']
        # Auth0 puts email in a custom namespaced claim on access tokens.
        # The standard 'email' claim is only present on ID tokens.
        return (
            claims.get('https://mystore.com/email') or
            claims.get('email') or
            ''
        )
    except (KeyError, AttributeError):
        return None
