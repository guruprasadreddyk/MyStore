# MyStore — Serverless E-Commerce Platform

A production-grade, fully serverless e-commerce platform built on AWS.

## Quick Links

- **Developer Guide:** [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md) — complete technical reference
- **API Spec:** [`openapi-spec.json`](openapi-spec.json) — OpenAPI 3.0

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Auth0, CloudFront + S3 |
| API | AWS API Gateway HTTP/2 + JWT Authorizer |
| Compute | AWS Lambda (Python 3.12) |
| Database | DynamoDB (pay-per-request) |
| Messaging | SNS + SQS |
| Auth | Auth0 (PKCE) |
| IaC | Terraform |
| Region | `ap-southeast-1` |

---

## Services (6 Lambdas)

| Lambda | Handles |
|---|---|
| `catalog_service` | Products, search, recommendations |
| `cart_service` | Cart, wishlist, saved addresses |
| `order_service` | Order creation, history, cancellation |
| `payment_service` | Payment processing, fulfillment trigger |
| `order_processor` | Async SQS consumer — marks orders shipped |
| `admin_service` | Admin dashboard, product & order management |

---

## Order Flow

```
Cart → Checkout (address + pricing) → Order created
→ Pay Now → Payment validated → status: paid
→ SQS → order_processor → status: shipped
```

---

## Quick Start

```powershell
# 1. Activate venv
.venv\Scripts\activate

# 2. Run tests
python run_tests.py

# 3. Build Lambdas
powershell -ExecutionPolicy Bypass -File scripts/build_lambdas.ps1

# 4. Deploy infrastructure
cd infrastructure && terraform apply -auto-approve && cd ..

# 5. Seed products
python scripts/seed_products.py

# 6. Deploy frontend
powershell -ExecutionPolicy Bypass -File scripts/deploy_frontend.ps1
```

---

## URLs (deployed)

- **Frontend:** CloudFront URL from `terraform output cloudfront_url`
- **API:** `https://hntwmrwmsl.execute-api.ap-southeast-1.amazonaws.com`

---

See [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md) for full documentation including every function, design decision, and known limitation.
