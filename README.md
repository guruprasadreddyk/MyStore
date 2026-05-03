# MyStore

> A production-grade, fully serverless e-commerce platform built on AWS.

React frontend · Python Lambdas · DynamoDB · Auth0 · Terraform IaC

---

## Features

**Shopping**
- 40 products across 5 categories (Books, Electronics, Clothing, Home & Kitchen, Sports & Fitness)
- Cursor-based pagination, category filters, price range, sort by price
- Full-text search with server-side price and category filtering
- Product recommendations based on cart contents
- Quick view modal, wishlist with cloud sync

**Cart & Checkout**
- Per-user cart with quantity controls (+ / −) and stock validation
- 7-day TTL auto-expiry on abandoned carts (DynamoDB native TTL)
- Checkout with Indian address form (state dropdown, phone + PIN validation)
- Pricing breakdown: subtotal + GST (18%) + delivery (free above ₹500)

**Orders & Payments**
- Full order lifecycle: `created → paid → shipped → delivered`
- Atomic inventory reservation at order creation (conditional DynamoDB writes)
- Order cancellation with automatic inventory rollback (only before payment)
- Payment processing with business-rule decline simulation (INSUFFICIENT_FUNDS, CARD_VELOCITY_EXCEEDED)
- Async fulfillment via SQS — orders marked shipped only after payment succeeds

**Account**
- Auth0 PKCE authentication (Google, email/password)
- Saved delivery addresses with default selection
- User profile: display name, phone, bio (stored in DynamoDB, synced to Auth0)
- Email verification via Auth0 Management API
- Order history with expandable pricing breakdown and delivery address

**Admin Panel** *(role-gated)*
- Dashboard: total orders, revenue, orders by status, low stock alerts, top products
- Product management: add, edit (price, stock, name, description), delete
- Order management: view all orders across all users, filter by status, update status

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (React 18 SPA)                   │
│                  Auth0 PKCE → JWT Bearer                    │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              CloudFront (CDN + SPA routing)                 │
│         S3 (static)  │  API Gateway (dynamic)              │
└──────────────────────┬──────────────────────────────────────┘
                       │ JWT Authorizer (Auth0)
         ┌─────────────┼──────────────────────────┐
         ▼             ▼                           ▼
  catalog_service  user_service            order_service
  products, search  cart, wishlist,        order CRUD,
  recommendations   addresses, profile     cancellation
                                                │
                   admin_service          payment_service
                   dashboard,             payment rules,
                   product & order mgmt   SQS trigger
                                                │
                                           SQS Queue
                                                │
                                                ▼
                                       order_processor
                                       status → shipped
                                       SNS notification
         │             │                       │
         └─────────────┴───────────────────────┘
                       │
         ┌─────────────┴──────────────────────────┐
         │              DynamoDB (5 tables)        │
         │  products_table_guru                    │
         │  cart_table_guru      (TTL enabled)     │
         │  orders_table_guru                      │
         │  wishlist_table_guru                    │
         │  user_data_table_guru (addresses+profile│
         └─────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Frontend | React 18, React Router v6 | SPA, no SSR |
| Auth | Auth0 (PKCE + M2M) | JWT, email verify, profile sync |
| Hosting | CloudFront + S3 | Private bucket, OAI, SPA routing fix |
| API | API Gateway HTTP/2 | JWT authorizer, 50 RPS / 100 burst |
| Compute | AWS Lambda, Python 3.12 | 6 functions, pay-per-invocation |
| Database | DynamoDB | 5 tables, pay-per-request, TTL on cart |
| Messaging | SNS + SQS | Async fulfillment, email notifications, DLQ |
| IaC | Terraform ≥ 1.0 | AWS provider ~6.0 |
| Tests | pytest + moto | 46 tests, full AWS mocking |

---

## Lambda Functions

| Function | Handles |
|---|---|
| `catalog_service_guru` | Products, search, recommendations (public) |
| `cart_service_guru` | Cart, wishlist, addresses, profile, Auth0 M2M |
| `order_service_guru` | Order CRUD, inventory reservation, cancellation |
| `payment_service_guru` | Payment processing, SQS fulfillment trigger |
| `processor_service_guru` | SQS consumer → marks orders shipped, SNS |
| `admin_service_guru` | Admin dashboard, product & order management |

---

## Order Flow

```
Add to cart → Checkout (address + pricing) → POST /order
    → inventory reserved atomically
    → cart cleared
    → status: created

Pay Now → POST /payment
    → amount validated against grand_total
    → business rules checked
    → status: paid
    → SQS message sent

order_processor (SQS trigger)
    → status: shipped
    → SNS shipping notification
```

---

## Quick Start

```powershell
# Activate virtual environment
.venv\Scripts\activate

# Run all 46 tests
python run_tests.py

# Build Lambda zip packages
powershell -ExecutionPolicy Bypass -File scripts/build_lambdas.ps1

# Deploy infrastructure (requires terraform.tfvars — see docs/DEPLOYMENT.md)
cd infrastructure
terraform apply -auto-approve
cd ..

# Seed 40 products into DynamoDB
python scripts/seed_products.py

# Build and deploy React frontend to S3 + CloudFront
powershell -ExecutionPolicy Bypass -File scripts/deploy_frontend.ps1
```

---

## Project Structure

```
MyStore/
├── services/
│   ├── utils.py              # Shared: response(), convert_decimal(), get_user_id()
│   ├── catalog_service.py    # Products, search, recommendations
│   ├── user_service.py       # Cart, wishlist, addresses, profile
│   ├── order_service.py      # Order lifecycle, inventory reservation
│   ├── payment_service.py    # Payment, decline rules, SQS trigger
│   ├── order_processor.py    # SQS consumer → shipped + SNS
│   └── admin_service.py      # Admin dashboard and management
├── tests/                    # 46 pytest tests (moto for AWS mocking)
├── frontend/
│   └── src/
│       ├── components/       # 16 React components
│       ├── hooks/            # 5 custom hooks (cart, orders, products, wishlist, recommendations)
│       └── services/api.js   # All API call functions
├── infrastructure/
│   ├── variables.tf          # All config variables
│   ├── terraform.tfvars      # Secret values (gitignored)
│   ├── lambda.tf             # 6 Lambda definitions + env vars
│   ├── api.tf                # API Gateway + 33 routes
│   ├── dynamodb.tf           # 5 DynamoDB tables
│   ├── messaging.tf          # SNS + SQS + DLQ
│   ├── frontend.tf           # S3 + CloudFront
│   └── iam.tf                # Lambda execution role
├── scripts/
│   ├── build_lambdas.ps1     # Packages each service + utils.py into zip
│   ├── deploy_frontend.ps1   # npm build → S3 sync → CloudFront invalidation
│   └── seed_products.py      # Seeds 40 products into DynamoDB
├── run_tests.py              # Test runner
└── openapi-spec.json         # OpenAPI 3.0 specification
```

---

## Tests

```
46 tests · 5 files · 0 failures
```

All AWS services are mocked with `moto` — no real AWS calls during tests.

```powershell
python run_tests.py
```

| File | Coverage |
|---|---|
| `test_product_service.py` | Product fetch, pagination |
| `test_search_service.py` | Search, price filter, category filter |
| `test_cart_service.py` | Add/remove/clear, stock validation |
| `test_order_service.py` | Order creation, address validation, inventory, cancellation |
| `test_payment_service.py` | Payment success, decline rules, amount mismatch |
