import json
import uuid
import os
import boto3
import urllib.request
import base64
from utils import response, send_email_via_resend, publish_sns_notification, update_order_status, get_table_name
from validation import validate

# Lazy-load tables for testability
def get_orders_table():
    return boto3.resource("dynamodb").Table(get_table_name("orders"))

def get_sqs_client():
    return boto3.client("sqs")

# Payment limits
MAX_PAYMENT_AMOUNT = 1_000_000
MIN_PAYMENT_AMOUNT = 1

# Simulated decline codes (used when Razorpay is not configured)
DECLINE_RULES = [
    {
        "code": "INSUFFICIENT_FUNDS",
        "message": "Payment declined: insufficient funds.",
        "condition": lambda amount, order: amount > 500_000
    },
    {
        "code": "CARD_VELOCITY_EXCEEDED",
        "message": "Payment declined: too many recent transactions.",
        "condition": lambda amount, order: len(order.get("items", [])) > 10
    },
]


def fetch_order(order_id):
    try:
        result = get_orders_table().get_item(Key={"order_id": order_id})
        return result.get("Item")
    except Exception as e:
        print(f"ERROR fetching order: {str(e)}")
        return None


def calculate_total(order):
    """Use grand_total if present (includes GST + delivery), else fall back to items sum."""
    if "grand_total" in order:
        return float(order["grand_total"])
    return sum(float(item["price"]) * int(item["quantity"]) for item in order.get("items", []))


def create_razorpay_order(amount_inr, receipt_id):
    """
    Create a Razorpay order. Amount must be in paise (INR × 100).
    Returns the Razorpay order object or None if not configured.
    Includes retry logic with exponential backoff.
    """
    # Read at call time to avoid cold-start env var injection issues
    key_id     = os.environ.get("RAZORPAY_KEY_ID", "")
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "")

    if not key_id or not key_secret:
        return None

    max_retries = 3
    for attempt in range(max_retries):
        try:
            payload = json.dumps({
                "amount":   int(amount_inr * 100),  # paise
                "currency": "INR",
                "receipt":  receipt_id[:40],
                "payment_capture": 1
            }).encode("utf-8")

            credentials = base64.b64encode(
                f"{key_id}:{key_secret}".encode()
            ).decode()

            req = urllib.request.Request(
                "https://api.razorpay.com/v1/orders",
                data    = payload,
                headers = {
                    "Content-Type":  "application/json",
                    "Authorization": f"Basic {credentials}"
                },
                method = "POST"
            )
            with urllib.request.urlopen(req, timeout=10) as res:
                result = json.loads(res.read())
                print(f"INFO: Razorpay order created — {result.get('id')}")
                return result
        except Exception as e:
            print(f"ERROR creating Razorpay order (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                import time
                time.sleep(2 ** attempt)
            else:
                print(f"ERROR: Failed to create Razorpay order after {max_retries} attempts")
                return None


def verify_razorpay_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    """Verify Razorpay payment signature using HMAC-SHA256."""
    import hmac
    import hashlib

    key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "")
    if not key_secret:
        return False

    message  = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected = hmac.new(
        key_secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, razorpay_signature)


def send_order_to_fulfillment_queue(order_id):
    """Trigger async fulfillment (shipped status) only after payment succeeds."""
    try:
        queue_name = os.environ.get('SQS_QUEUE_NAME', 'order-processing-queue-guru')
        sqs = get_sqs_client()
        queue_url = sqs.get_queue_url(QueueName=queue_name)['QueueUrl']
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps({"order_id": order_id})
        )
        print(f"INFO: Order {order_id} sent to fulfillment queue")
    except Exception as e:
        print(f"ERROR sending to fulfillment queue: {str(e)}")


def publish_payment_notification(order_id, payment_status, order=None, decline_code=None):
    try:
        name           = order.get('address', {}).get('full_name', 'there') if order else 'there'
        grand_total    = int(order.get('grand_total', 0)) if order else 0
        customer_email = order.get('user_email', '') if order else ''
        order_ref      = order_id[:8].upper()

        # SNS (admin)
        subject = f"Payment {'Confirmed' if payment_status=='success' else 'Failed'}: #{order_ref}"
        msg     = f"Order #{order_ref} — {name} ({customer_email}) — ₹{grand_total:,} — {payment_status}"
        if decline_code:
            msg += f" — {decline_code}"
        publish_sns_notification(subject=subject, message=msg)

        # Resend (customer)
        if payment_status == 'success':
            send_email_via_resend(
                to_email  = customer_email,
                subject   = f"Payment Confirmed — #{order_ref} | MyStore",
                html_body = f"""<div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
<h2 style="color:#10b981">✅ Payment Confirmed</h2>
<p>Hi <strong>{name}</strong>, your payment of <strong>₹{grand_total:,}</strong> for order <strong>#{order_ref}</strong> was successful.</p>
<p>Your order is being processed and will be shipped soon.</p>
<hr style="border:none;border-top:1px solid #eee;margin:24px 0"/>
<p style="font-size:0.8rem;color:#999">MyStore · This is an automated email.</p>
</div>""",
                text_body = f"Hi {name}, payment of ₹{grand_total:,} for order #{order_ref} confirmed. Your order is being processed."
            )
        else:
            send_email_via_resend(
                to_email  = customer_email,
                subject   = f"Payment Failed — #{order_ref} | MyStore",
                html_body = f"""<div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
<h2 style="color:#ef4444">❌ Payment Failed</h2>
<p>Hi <strong>{name}</strong>, we could not process your payment for order <strong>#{order_ref}</strong>.</p>
<p><strong>Reason:</strong> {decline_code or 'Payment declined'}</p>
<p>Please try again with a different payment method.</p>
<hr style="border:none;border-top:1px solid #eee;margin:24px 0"/>
<p style="font-size:0.8rem;color:#999">MyStore · This is an automated email.</p>
</div>""",
                text_body = f"Hi {name}, payment for order #{order_ref} failed. Reason: {decline_code or 'declined'}. Please try again."
            )
    except Exception as e:
        # Notification failure must never crash the payment handler
        print(f"WARN: Failed to send payment notification for {order_id}: {str(e)}")


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

        # 🔹 POST /payment/create-order → create Razorpay order (returns key + rzp order id)
        if path == "/payment/create-order" and method == "POST":
            body     = json.loads(event.get("body") or "{}")
            order_id = body.get("order_id")

            if not order_id:
                return response(400, message="order_id is required")

            order = fetch_order(order_id)
            if not order:
                return response(400, message="Invalid order: order not found")
            if order.get("status") == "paid":
                return response(400, message="Order has already been paid")

            amount = calculate_total(order)

            # Try Razorpay first; fall back to simulation if not configured
            rzp_order = create_razorpay_order(amount, order_id)
            if rzp_order:
                return response(200, data={
                    "razorpay_key_id":   os.environ.get("RAZORPAY_KEY_ID", ""),
                    "razorpay_order_id": rzp_order["id"],
                    "amount":            rzp_order["amount"],
                    "currency":          "INR",
                    "order_id":          order_id,
                    "mode":              "razorpay"
                })
            else:
                # Razorpay not configured — return simulation mode
                return response(200, data={
                    "razorpay_key_id":  None,
                    "razorpay_order_id": None,
                    "amount":           int(amount * 100),
                    "currency":         "INR",
                    "order_id":         order_id,
                    "mode":             "simulation"
                })

        # 🔹 POST /payment → verify Razorpay payment or run simulation
        if path == "/payment" and method == "POST":
            body = json.loads(event.get("body") or "{}")

            # Validate input
            try:
                validate(body, "create_payment")
            except ValueError as e:
                return response(400, message=str(e))

            order_id = body.get("order_id")
            amount   = body.get("amount")

            try:
                amount = float(amount)
            except (TypeError, ValueError):
                return response(400, message="amount must be a valid number")

            # Fetch and validate order
            order = fetch_order(order_id)
            if not order:
                return response(400, message="Invalid order: order not found")

            if order.get("status") == "paid":
                return response(400, message="Order has already been paid")

            # Verify amount matches order grand total (includes GST + delivery)
            actual_total = calculate_total(order)
            if abs(amount - actual_total) > 0.01:
                return response(400, message=f"Amount mismatch: received {amount:.2f}, expected {actual_total:.2f}")

            # Run payment through processor
            success, payment, decline_code, message = process_payment(order_id, amount, order)

            # If Razorpay payment details provided, verify signature instead of simulation
            rzp_order_id   = body.get("razorpay_order_id")
            rzp_payment_id = body.get("razorpay_payment_id")
            rzp_signature  = body.get("razorpay_signature")

            if rzp_order_id and rzp_payment_id and rzp_signature:
                # Real Razorpay payment — verify signature
                if verify_razorpay_payment(rzp_order_id, rzp_payment_id, rzp_signature):
                    success      = True
                    decline_code = None
                    message      = "Payment successful"
                    payment      = {
                        "payment_id":  rzp_payment_id,
                        "order_id":    order_id,
                        "amount":      amount,
                        "status":      "success",
                        "decline_code": None,
                        "mode":        "razorpay"
                    }
                else:
                    success      = False
                    decline_code = "SIGNATURE_INVALID"
                    message      = "Payment verification failed: invalid signature"
                    payment      = {
                        "payment_id":  str(uuid.uuid4()),
                        "order_id":    order_id,
                        "amount":      amount,
                        "status":      "failed",
                        "decline_code": "SIGNATURE_INVALID",
                        "mode":        "razorpay"
                    }

            if success:
                update_order_status(order_id, "paid")
                if order.get("email_verified", True):
                    publish_payment_notification(order_id, "success", order=order)
                else:
                    print(f"WARN: Skipping payment confirmation email for order {order_id} — email not verified")
                send_order_to_fulfillment_queue(order_id)
                return response(200, data=payment, message=message)
            else:
                if order.get("email_verified", True):
                    publish_payment_notification(order_id, "failed", order=order, decline_code=decline_code)
                return response(400, data=payment, message=message)

        # 🔹 Invalid route
        return response(404, message="Route not found")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return response(500, message="Internal server error")
