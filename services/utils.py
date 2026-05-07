import json
import os
import boto3
from decimal import Decimal
from datetime import datetime


# ─── Table name resolution (env var → default) ───────────────────────────────

def get_table_name(key):
    """
    Resolve DynamoDB table names from env vars so they can be overridden
    per environment without code changes.
    """
    defaults = {
        "products":  "products_table_guru",
        "orders":    "orders_table_guru",
        "cart":      "cart_table_guru",
        "wishlist":  "wishlist_table_guru",
        "user_data": "user_data_table_guru",
        "reviews":   "reviews_table_guru",
        "returns":   "returns_table_guru",
    }
    env_keys = {
        "products":  "PRODUCTS_TABLE",
        "orders":    "ORDERS_TABLE",
        "cart":      "CART_TABLE",
        "wishlist":  "WISHLIST_TABLE",
        "user_data": "USER_DATA_TABLE",
        "reviews":   "REVIEWS_TABLE",
        "returns":   "RETURNS_TABLE",
    }
    return os.environ.get(env_keys[key], defaults[key])


# 🔹 Update order status with history tracking (shared across services)
def update_order_status(order_id, new_status, message=None):
    """Update order status and append to status_history. Non-fatal on error."""
    try:
        timestamp     = datetime.utcnow().isoformat() + "Z"
        history_entry = {
            "status":    new_status,
            "timestamp": timestamp,
            "message":   message or f"Order status changed to {new_status}"
        }
        boto3.resource("dynamodb").Table(get_table_name("orders")).update_item(
            Key={"order_id": str(order_id)},
            UpdateExpression="SET #s = :status, #h = list_append(if_not_exists(#h, :empty), :entry)",
            ExpressionAttributeNames={"#s": "status", "#h": "status_history"},
            ExpressionAttributeValues={
                ":status": new_status,
                ":entry":  [history_entry],
                ":empty":  []
            }
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


# 🔹 Send email via Gmail SMTP with retry logic
def send_email_via_resend(to_email, subject, html_body, text_body=""):
    """Send transactional email via Gmail SMTP. Non-fatal — logs error if it fails."""
    import smtplib
    import time
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    smtp_user     = os.environ.get("SMTP_USER", "")       # your Gmail address
    smtp_password = os.environ.get("SMTP_PASSWORD", "")   # Gmail App Password
    smtp_from     = os.environ.get("SMTP_FROM", smtp_user) # display name + address

    if not smtp_user or not smtp_password:
        print("INFO: SMTP_USER / SMTP_PASSWORD not configured — email not sent.")
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
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = smtp_from
            msg["To"]      = to_email

            if text_body:
                msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, to_email, msg.as_string())

            print(f"INFO: Email sent via Gmail SMTP to {to_email} — {subject}")
            return  # success
        except Exception as e:
            print(f"ERROR sending email via Gmail SMTP (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # exponential backoff: 1s, 2s
            else:
                print(f"ERROR: Failed to send email after {max_retries} attempts")


# 🔹 Fetch product from DynamoDB
def fetch_product(product_id):
    """Fetch a single product by ID from DynamoDB."""
    try:
        result = boto3.resource("dynamodb").Table(get_table_name("products")).get_item(Key={"id": str(product_id)})
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
        # Guard against non-string values (e.g. boolean True from a misconfigured Action)
        for key in ('https://mystore.com/email', 'email'):
            val = claims.get(key)
            if val and isinstance(val, str):
                return val
        return ''
    except (KeyError, AttributeError):
        return None


# 🔹 Extract email_verified flag from Auth0 JWT Authorizer
def get_email_verified(event):
    try:
        claims = event['requestContext']['authorizer']['jwt']['claims']
        verified = claims.get('https://mystore.com/email_verified')
        if verified is None:
            # Claim not present — Auth0 Action not yet updated, allow emails through
            return True
        # JWT claims come through as strings
        if isinstance(verified, str):
            return verified.lower() == 'true'
        return bool(verified)
    except (KeyError, AttributeError):
        return True  # fail open — don't block emails on missing claim
