import json
from decimal import Decimal

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
        body["data"] = data
        
    if message is not None:
        body["message"] = message

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
        return "user1"
