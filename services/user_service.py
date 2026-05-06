"""
user_service.py — handles all user-scoped data:
  - Cart          → cart_table_guru
  - Wishlist      → wishlist_table_guru
  - Addresses     → user_data_table_guru (field: addresses)
  - Profile       → user_data_table_guru (field: profile)
  - Auth0 actions → email verification, name sync via Management API
"""

import json
import uuid
import os
import time
import urllib.request
import boto3
from utils import response, send_email_via_resend
from validation import validate

# Lazy-load tables for testability
def get_cart_table():
    return boto3.resource("dynamodb").Table('cart_table_guru')

def get_wishlist_table():
    return boto3.resource("dynamodb").Table('wishlist_table_guru')

def get_user_data_table():
    return boto3.resource("dynamodb").Table('user_data_table_guru')

CART_TTL_SECONDS = 7 * 24 * 60 * 60

AUTH0_DOMAIN            = os.environ.get("AUTH0_DOMAIN",            "dev-sjgq3v6pvbgxs6mb.us.auth0.com")
AUTH0_M2M_CLIENT_ID     = os.environ.get("AUTH0_M2M_CLIENT_ID",     "")
AUTH0_M2M_CLIENT_SECRET = os.environ.get("AUTH0_M2M_CLIENT_SECRET", "")


# ─── Auth0 Management API helpers ────────────────────────────────────────────

def get_management_token():
    if not AUTH0_M2M_CLIENT_ID or not AUTH0_M2M_CLIENT_SECRET:
        raise ValueError("AUTH0_M2M_CLIENT_ID and AUTH0_M2M_CLIENT_SECRET env vars not set")

    payload = json.dumps({
        "client_id":     AUTH0_M2M_CLIENT_ID,
        "client_secret": AUTH0_M2M_CLIENT_SECRET,
        "audience":      f"https://{AUTH0_DOMAIN}/api/v2/",
        "grant_type":    "client_credentials"
    }).encode("utf-8")

    req = urllib.request.Request(
        f"https://{AUTH0_DOMAIN}/oauth/token",
        data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        return json.loads(res.read())["access_token"]


def send_verification_email(user_id):
    token   = get_management_token()
    payload = json.dumps({"user_id": user_id, "client_id": AUTH0_M2M_CLIENT_ID}).encode("utf-8")
    req = urllib.request.Request(
        f"https://{AUTH0_DOMAIN}/api/v2/jobs/verification-email",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        return json.loads(res.read())


def update_auth0_name(user_id, name):
    """
    Sync display_name to Auth0 user profile so the dashboard shows the real name.
    Requires update:users scope on the M2M app.
    """
    token   = get_management_token()
    # Auth0 user_id contains '|' which must be URL-encoded
    encoded = urllib.request.quote(user_id, safe="")
    payload = json.dumps({"name": name}).encode("utf-8")
    req = urllib.request.Request(
        f"https://{AUTH0_DOMAIN}/api/v2/users/{encoded}",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="PATCH"
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        return json.loads(res.read())


# ─── Product fetch ────────────────────────────────────────────────────────────

from utils import fetch_product, convert_decimal, get_user_id


# ─── Cart helpers ─────────────────────────────────────────────────────────────

def get_cart(user_id):
    res = get_cart_table().get_item(Key={"user_id": user_id})
    return res.get("Item", {}).get("cart", [])


def save_cart(user_id, cart):
    get_cart_table().put_item(Item={
        "user_id": user_id,
        "cart":    cart,
        "ttl":     int(time.time()) + CART_TTL_SECONDS
    })


# ─── Wishlist helpers ─────────────────────────────────────────────────────────

def get_wishlist(user_id):
    res = get_wishlist_table().get_item(Key={"user_id": user_id})
    return res.get("Item", {}).get("wishlist", [])


def save_wishlist(user_id, wishlist):
    get_wishlist_table().put_item(Item={"user_id": user_id, "wishlist": wishlist})


# ─── Address helpers ──────────────────────────────────────────────────────────

def get_addresses(user_id):
    res = get_user_data_table().get_item(Key={"user_id": user_id})
    return res.get("Item", {}).get("addresses", [])


def save_addresses(user_id, addresses):
    get_user_data_table().update_item(
        Key={"user_id": user_id},
        UpdateExpression="SET addresses = :a",
        ExpressionAttributeValues={":a": addresses}
    )


# ─── Profile helpers ──────────────────────────────────────────────────────────

def get_profile(user_id):
    res = get_user_data_table().get_item(Key={"user_id": user_id})
    return res.get("Item", {}).get("profile", {})


def save_profile(user_id, profile):
    get_user_data_table().update_item(
        Key={"user_id": user_id},
        UpdateExpression="SET #p = :profile",
        ExpressionAttributeNames={"#p": "profile"},
        ExpressionAttributeValues={":profile": profile}
    )


# ─── Lambda handler ───────────────────────────────────────────────────────────

def lambda_handler(event, context):
    try:
        user_id = get_user_id(event)
        path    = event.get("rawPath") or event.get("path", "")
        method  = event.get("requestContext", {}).get("http", {}).get("method", "")

        if path.startswith("/v1/"):
            path = path[3:]

        print(f"INFO: Path={path}, Method={method}, User={user_id}")

        # ── Cart ──────────────────────────────────────────────────────────────

        if path == "/cart" and method == "GET":
            return response(200, data=convert_decimal(get_cart(user_id)))

        if path == "/cart/add" and method == "POST":
            body = json.loads(event.get("body") or "{}")
            
            # Validate input
            try:
                validate(body, "add_to_cart")
            except ValueError as e:
                return response(400, message=str(e))
            
            extra = set(body.keys()) - {"id", "variant_id"}
            if extra:
                return response(400, message=f"Unexpected fields: {list(extra)}. Only 'id' and 'variant_id' are allowed")

            product_id = str(body.get("id", ""))
            variant_id = body.get("variant_id")  # Optional
            if not product_id:
                return response(400, message="Product ID required")

            product = fetch_product(product_id)
            if not product:
                return response(400, message="Invalid product")

            # If variant_id provided, validate it exists
            if variant_id:
                variants = product.get("variants", [])
                variant = next((v for v in variants if v.get("variant_id") == variant_id), None)
                if not variant:
                    return response(400, message=f"Invalid variant: {variant_id}")
                variant_price = variant.get("price", product["price"])
                variant_stock = variant.get("stock", product.get("stock_quantity", 0))
            else:
                # No variant specified — use product defaults
                variant_price = product["price"]
                variant_stock = product.get("stock_quantity", 0)

            if variant_stock <= 0:
                return response(400, message="Product is out of stock")

            cart = get_cart(user_id)
            # Count items with same product_id AND variant_id (if specified)
            qty_in_cart = sum(
                i.get("quantity", 1) for i in cart 
                if str(i.get("id")) == product_id and i.get("variant_id") == variant_id
            )
            if qty_in_cart >= variant_stock:
                return response(400, message=f"Cannot add more. Only {variant_stock} available in stock")

            validated = {
                "id":       product["id"],
                "name":     product["name"],
                "price":    variant_price,
                "category": product.get("category", "General")
            }
            if variant_id:
                validated["variant_id"] = variant_id

            # Find existing cart item with same product_id AND variant_id
            existing = next(
                (i for i in cart if str(i.get("id")) == str(validated["id"]) and i.get("variant_id") == variant_id),
                None
            )
            if existing:
                existing["quantity"] += 1
            else:
                validated["quantity"] = 1
                cart.append(validated)
            save_cart(user_id, cart)
            return response(200, data=convert_decimal(cart), message="Item added")

        if path.startswith("/cart/remove/") and method == "DELETE":
            item_id    = path.split("/")[-1]
            # Optional variant_id from query string to distinguish variants
            qp         = event.get("queryStringParameters") or {}
            variant_id = qp.get("variant_id")
            cart       = get_cart(user_id)
            item_found = False
            for item in cart:
                id_match      = str(item.get("id")) == str(item_id)
                variant_match = item.get("variant_id") == variant_id  # both None = match
                if id_match and variant_match:
                    item_found = True
                    if item.get("quantity", 1) > 1:
                        item["quantity"] -= 1
                    else:
                        cart = [i for i in cart if not (
                            str(i.get("id")) == str(item_id) and i.get("variant_id") == variant_id
                        )]
                    break
            if not item_found:
                return response(404, message="Item not found in cart")
            save_cart(user_id, cart)
            return response(200, data=convert_decimal(cart), message="Item removed")

        if path == "/cart" and method == "DELETE":
            save_cart(user_id, [])
            return response(200, message="Cart cleared")

        # ── Wishlist ──────────────────────────────────────────────────────────

        if path == "/wishlist" and method == "GET":
            return response(200, data=convert_decimal(get_wishlist(user_id)))

        if path == "/wishlist/add" and method == "POST":
            body = json.loads(event.get("body") or "{}")
            extra = set(body.keys()) - {"id"}
            if extra:
                return response(400, message=f"Unexpected fields: {list(extra)}. Only 'id' is allowed")
            product_id = str(body.get("id", ""))
            if not product_id:
                return response(400, message="Product ID required")
            product = fetch_product(product_id)
            if not product:
                return response(400, message="Invalid product")
            wishlist = get_wishlist(user_id)
            if any(str(i.get("id")) == product_id for i in wishlist):
                return response(400, message="Item already in wishlist")
            wishlist.append({
                "id":       product["id"],
                "name":     product["name"],
                "price":    product["price"],
                "category": product.get("category", "General"),
                "image_url":product.get("image_url", "")
            })
            save_wishlist(user_id, wishlist)
            return response(200, data=convert_decimal(wishlist), message="Item added to wishlist")

        if path.startswith("/wishlist/remove/") and method == "DELETE":
            item_id      = path.split("/")[-1]
            wishlist     = get_wishlist(user_id)
            new_wishlist = [i for i in wishlist if str(i.get("id")) != str(item_id)]
            if len(new_wishlist) == len(wishlist):
                return response(404, message="Item not found in wishlist")
            save_wishlist(user_id, new_wishlist)
            return response(200, data=convert_decimal(new_wishlist), message="Item removed from wishlist")

        # ── Addresses ─────────────────────────────────────────────────────────

        if path == "/addresses" and method == "GET":
            return response(200, data=get_addresses(user_id))

        if path == "/addresses" and method == "POST":
            body     = json.loads(event.get("body") or "{}")
            
            # Validate input
            try:
                validate(body, "add_address")
            except ValueError as e:
                return response(400, message=str(e))
            
            addresses   = get_addresses(user_id)
            new_address = {
                "address_id":    str(uuid.uuid4()),
                "full_name":     body["full_name"].strip(),
                "phone":         body["phone"].strip(),
                "address_line1": body["address_line1"].strip(),
                "address_line2": body.get("address_line2", "").strip(),
                "city":          body["city"].strip(),
                "state":         body["state"].strip(),
                "pincode":       body["pincode"].strip(),
                "is_default":    len(addresses) == 0
            }
            addresses.append(new_address)
            save_addresses(user_id, addresses)
            return response(200, data=addresses, message="Address saved")

        if path.startswith("/addresses/") and method == "PUT":
            address_id = path.split("/")[-1]
            addresses  = get_addresses(user_id)
            found      = False
            for addr in addresses:
                addr["is_default"] = (addr["address_id"] == address_id)
                if addr["address_id"] == address_id:
                    found = True
            if not found:
                return response(404, message="Address not found")
            save_addresses(user_id, addresses)
            return response(200, data=addresses, message="Default address updated")

        if path.startswith("/addresses/") and method == "DELETE":
            address_id    = path.split("/")[-1]
            addresses     = get_addresses(user_id)
            new_addresses = [a for a in addresses if a["address_id"] != address_id]
            if len(new_addresses) == len(addresses):
                return response(404, message="Address not found")
            if new_addresses and not any(a["is_default"] for a in new_addresses):
                new_addresses[0]["is_default"] = True
            save_addresses(user_id, new_addresses)
            return response(200, data=new_addresses, message="Address deleted")

        # ── Profile ───────────────────────────────────────────────────────────

        if path == "/profile/me" and method == "GET":
            return response(200, data=get_profile(user_id))

        if path == "/profile/me" and method == "PUT":
            body    = json.loads(event.get("body") or "{}")
            
            # Validate input
            try:
                validate(body, "update_profile")
            except ValueError as e:
                return response(400, message=str(e))
            
            allowed = {"display_name", "phone", "bio"}
            profile = {k: str(v).strip() for k, v in body.items() if k in allowed and str(v).strip()}

            save_profile(user_id, profile)

            # Sync display_name to Auth0 so the dashboard shows the real name
            if "display_name" in profile:
                try:
                    update_auth0_name(user_id, profile["display_name"])
                    print(f"INFO: Auth0 name updated for {user_id}")
                except Exception as e:
                    # Non-fatal — profile saved in DynamoDB regardless
                    print(f"WARN: Auth0 name sync failed: {str(e)}")

            return response(200, data=profile, message="Profile updated")

        if path == "/profile/verify-email" and method == "POST":
            try:
                result = send_verification_email(user_id)
                print(f"INFO: Verification email job: {result.get('id')}")
                return response(200, message="Verification email sent. Please check your inbox.")
            except ValueError as e:
                print(f"ERROR: M2M not configured: {str(e)}")
                return response(503, message="Email verification service not configured.")
            except Exception as e:
                print(f"ERROR sending verification email: {str(e)}")
                return response(500, message="Failed to send verification email. Please try again.")

        return response(404, message="Route not found")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return response(500, message="Internal server error")
