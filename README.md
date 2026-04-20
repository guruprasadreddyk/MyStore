# E-commerce Platform: Complete Architecture & Infrastructure Guide

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Breakdown](#component-breakdown)
3. [Data Flow Examples](#data-flow-examples)
4. [AWS Console Navigation](#aws-console-navigation)
5. [Testing Guide](#testing-guide)
6. [API Documentation](#api-documentation)
7. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### Complete System Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER (Browser)                      │
│                     React 18.2 SPA (Frontend)                  │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTPS Requests
┌────────────────────────▼─────────────────────────────────────┐
│                 CDN & STATIC HOSTING LAYER                    │
│  CloudFront Distribution (Global CDN)                         │
│    ├─ Origin 1: S3 Bucket (Static Assets)                    │
│    └─ Origin 2: API Gateway (Dynamic Routes)                 │
└────────────────────────┬─────────────────────────────────────┘
                         │ Routes requests to backend
┌────────────────────────▼─────────────────────────────────────┐
│                    API GATEWAY LAYER                          │
│          HTTP/2 API Gateway (12 Routes)                       │
│  Throttle: 50 RPS steady + 100 RPS burst                     │
└─────────────┬──────────────────────────────────────────────┬──┘
              │ Routes to Lambda functions                    │
    ┌─────────┼──────────────────────────┬───────────────────┘
    │         │                          │
┌───▼──┐ ┌───▼──┐ ┌──────┐ ┌──────────┐ ┌──────────┐
│Prod  │ │Cart  │ │Order │ │Payment   │ │Search    │
│Svc   │ │Svc   │ │Svc   │ │Svc       │ │Svc       │
│(λ)   │ │(λ)   │ │(λ)   │ │(λ)       │ │(λ)       │
└──┬───┘ └──┬───┘ └───┬──┘ └────┬─────┘ └──────────┘
   │        │         │        │
   └────────┼─────────┼────────┘
            │         │
┌───────────▼─────────▼──────────────────────┐
│           DATA LAYER (DynamoDB)            │
│  Products Table | Cart Table | Orders Tbl  │
│  (Pay-per-request billing)                 │
└────────────────────────────────────────────┘

            ┌──────────────────────────────┐
            │   MESSAGING LAYER            │
            │  (SQS & SNS)                 │
            │                              │
            │  SNS Topic (Notifications)   │
            │      ↓                       │
            │  SQS Queue (Order Processing)│
            │      ↓                       │
            │  Order Processor Lambda (λ)  │
            │                              │
            └──────────────────────────────┘
```

### Key Characteristics

| Aspect | Details |
|--------|---------|
| **Architecture** | Serverless microservices with event-driven messaging |
| **Deployment** | Infrastructure-as-Code (Terraform) |
| **Scalability** | Auto-scaling (Lambda & DynamoDB on-demand) |
| **Data Model** | NoSQL (DynamoDB pay-per-request) |
| **API Type** | HTTP/2 API Gateway with versioning |
| **Messaging** | Async pub/sub (SNS) + queue (SQS) |
| **Frontend Hosting** | CloudFront + S3 with Origin Access Identity |
| **Testing** | 35 comprehensive unit tests with moto mocking |
| **Documentation** | OpenAPI 3.0 specification with Swagger |

---

## Recent Updates (April 2026)

### ✅ **Enhanced Testing Suite**
- **35 Unit Tests**: Complete coverage for all 5 services
- **Mocking Framework**: Moto for AWS service simulation
- **Test Categories**:
  - Product Service: 5 tests (CRUD, seeding, error handling)
  - Cart Service: 8 tests (add/remove/clear, stock validation)
  - Order Service: 7 tests (creation, validation, status updates)
  - Payment Service: 7 tests (processing, validation, error scenarios)
  - Search Service: 8 tests (search functionality, edge cases)

### ✅ **API Versioning Implementation**
- **Versioned Endpoints**: All 12 API endpoints now support `/v1/` prefixed paths
- **Backward Compatibility**: Lambda handlers strip `/v1` prefix for seamless routing
- **API Gateway Stage**: v1 stage deployed with access logging
- **Path Support**: Both `/products` and `/v1/products` work identically

### ✅ **Lambda Handler Updates**
- **Version-Aware Routing**: All 5 services updated to handle versioned paths
- **Path Stripping Logic**: Automatic `/v1` prefix removal before route matching
- **Consistent Behavior**: Same functionality for versioned and non-versioned endpoints
- **Authentication**: Bearer token security scheme

### ✅ **Production Readiness**
- **Error Handling**: Consistent response formats across all services
- **Input Validation**: Comprehensive parameter validation
- **Logging**: Structured logging for debugging and monitoring

### ❌ **Observability (Removed)**
- **CloudWatch Monitoring**: Removed due to AWS access limitations
- **Implementation Guide**: See observability implementation notes below
- **Alternative**: Use built-in CloudWatch logs and basic Lambda monitoring

### 📊 **Test Results**
```
Test Summary: 35 passed, 0 failed
├── Product Service: 5/5 passed
├── Cart Service: 8/8 passed
├── Order Service: 7/7 passed
├── Payment Service: 7/7 passed
└── Search Service: 8/8 passed
```

---

## Component Breakdown

## Component Breakdown

### 1. FRONTEND (React SPA)

**Purpose:** User-facing single-page application for browsing products, managing cart, placing orders, and processing payments.

**Technology Stack:**
- React 18.2
- react-scripts 5.0.1
- ES6+ JavaScript

**Core Features:**
- Product browsing with category filtering
- Real-time search with fallback logic
- Shopping cart management
- Order placement
- Payment processing
- Order history viewing

**Key Files:**
- `frontend/src/App.js` - Main component with all business logic
- `frontend/package.json` - Dependencies and scripts
- `frontend/public/index.html` - Entry point
- `frontend/build/` - Production bundled code

**API Base URL:**
- Development: Relative URLs (uses CloudFront domain)
- It's configured dynamically during deployment

**State Management:**
- React hooks (useState, useEffect)
- Local component state

**AWS Console Check:**
- CloudFront → Distributions → Find by domain name
  - View request metrics under "Monitoring" tab
  - Check cache hit ratio under "Statistics"
  - Monitor real-time requests/bandwidth

---

### 2. CDN & STATIC HOSTING (CloudFront + S3)

**Purpose:** Serve frontend assets globally with low latency and high availability. Keep S3 bucket private using Origin Access Identity.

**Architecture:**
```
User Browser
    ↓
CloudFront (Global Edge Locations)
    ├─ CDN Cache
    ├─ Origin 1: S3 Bucket (Static assets)
    │   └─ index.html, CSS, JS bundles
    └─ Origin 2: API Gateway (Dynamic routes)
        └─ /products, /cart, /order, etc.
```

**S3 Bucket Configuration:**
- **Bucket Name:** `ecommerce-frontend-guru-{random-8-chars}`
- **Public Access:** Blocked (all)
- **Versioning:** Enabled (for rollback)
- **Objects:** HTML/CSS/JS from React build output

**CloudFront Distribution:**
- **Default Root Object:** index.html
- **SSL/TLS:** HTTPS enforced (redirects HTTP to HTTPS)
- **Cache Behaviors:**
  - `/index.html` → S3 (cache)
  - `/static/*` → S3 (cache long-lived)
  - `/products*` → API Gateway (no cache or short cache)
  - `/search*` → API Gateway (forward query strings)
  - `/cart*` → API Gateway
  - `/order*` → API Gateway
  - `/payment*` → API Gateway

**Origin Access Identity (OAI):**
- CloudFront uses OAI to access S3 privately
- S3 bucket policy only allows OAI (not public)
- Prevents direct access to S3 bucket

**AWS Console Navigation:**

1. **S3 Bucket Contents:**
   - AWS Console → S3 → Buckets
   - Search for `ecommerce-frontend-guru`
   - Click bucket → Objects tab
   - See index.html, css/, js/ folders
   - Check "Versions" if you want to rollback

2. **Monitor S3 Storage:**
   - S3 → Bucket → Metrics tab
   - View total storage size
   - Number of objects stored

3. **CloudFront Distribution:**
   - AWS Console → CloudFront → Distributions
   - Click on the distribution domain name
   - **General tab:** Check SSL certificate, origins, behaviors
   - **Origins tab:** See S3 and API Gateway as origins
   - **Behaviors tab:** See cache rules for each path
   - **Invalidations tab:** Check if cache invalidation was triggered

4. **Monitor CloudFront Performance:**
   - CloudFront → Distributions → Click distribution
   - Monitoring tab:
     - **Requests:** Real-time count of requests
     - **Bytes Downloaded/Uploaded:** Data transfer metrics
     - **Cache Statistics:** Hit/Miss ratio
     - **4xx/5xx Errors:** Error rate

5. **Cache Invalidation:**
   - CloudFront → Distributions → Click distribution
   - Invalidations tab → Create invalidation
   - Pattern: `/static/*` to refresh all assets
   - Monitor invalidation status

---

### 3. API GATEWAY (HTTP/2 API)

**Purpose:** Single entry point for all backend API requests. Routes requests to appropriate Lambda functions, enforces rate limiting, and handles CORS.

**API Details:**
- **Type:** HTTP API v2 (lightweight alternative to REST API)
- **Name:** API_Services_Guru
- **Protocol:** HTTP/2
- **CORS:** Enabled for all origins (`*`)
- **Rate Limiting:** 50 RPS steady-state, 100 RPS burst
- **Auto-Deploy:** Stage auto-deploys on changes
- **Versioning:** v1 stage with access logging enabled

**API Endpoints:**
- **Base URL:** `https://[api-gateway-id].execute-api.[region].amazonaws.com/v1/`
- **Documentation:** OpenAPI 3.0 spec available at `openapi-spec.json`
- **Authentication:** Bearer token (configured in OpenAPI spec)

**12 Routes:**

| Route | Method | Handler | Purpose |
|-------|--------|---------|---------|
| `/v1/products` | GET | product_service | List all products |
| `/v1/products/{id}` | GET | product_service | Get product details |
| `/v1/search` | GET | search_service | Search products by query |
| `/v1/cart` | GET | cart_service | Get current cart |
| `/v1/cart/add` | POST | cart_service | Add item to cart |
| `/v1/cart/remove/{id}` | DELETE | cart_service | Remove item from cart |
| `/v1/cart` | DELETE | cart_service | Clear entire cart |
| `/v1/order` | GET | order_service | Get order history |
| `/v1/order` | POST | order_service | Create new order |
| `/v1/order/{id}` | GET | order_service | Get order details |
| `/v1/order/{id}` | PUT | order_service | Update order status |
| `/v1/payment` | POST | payment_service | Process payment |

**AWS Console Navigation:**

1. **View API Configuration:**
   - AWS Console → API Gateway
   - APIs → Click "API_Services_Guru"
   - **Overview tab:** See API endpoint URL
   - **Routes tab:** See all 12 routes with HTTP methods
   - **Integrations tab:** See Lambda function mappings

2. **Check Rate Limiting:**
   - API Gateway → APIs → API_Services_Guru
   - Settings → Throttle Settings
   - See 50 RPS steady-state, 100 RPS burst limits

3. **Monitor API Requests:**
   - API Gateway → APIs → API_Services_Guru
   - Stages → *$default → Metrics
   - View:
     - Count (number of requests)
     - 4xx Errors (client errors)
     - 5xx Errors (server errors)
     - Latency (response time)
     - Data Transferred

4. **View Request Logs:**
   - CloudWatch → Log Groups
   - `/aws/api-gateway/API_Services_Guru`
   - See detailed logs for each API request/response

5. **Test API Endpoints (Manual):**
   - API Gateway → APIs → API_Services_Guru
   - Routes → Select route → Test
   - Send test request and see response

---

### 4. LAMBDA FUNCTIONS (Compute Layer)

**Purpose:** Serverless compute for business logic. Each function handles one domain and is triggered by API Gateway or SQS.

**Runtime:** Python 3.12

**Common Configuration:**
- **Memory:** 128 MB (default, sufficient for I/O operations)
- **Timeout:** 30 seconds (Lambda default)
- **Execution Role:** lambda_exec_role (with DynamoDB, SQS, SNS permissions)
- **API Versioning:** All handlers support `/v1/` prefixed paths with automatic prefix stripping

#### **4.1 Product Service Lambda**

**File:** `product_service.py`

**Handler:** `product_service.lambda_handler`

**Triggers:**
- API Gateway: GET /products
- API Gateway: GET /products/{id}

**Functions:**
1. **GET /products** → Returns all 12 products (seeded on first call)
2. **GET /products/{id}** → Returns specific product details

**Database Operations:**
- Query `products_table_guru` 
- Scan to get all products
- Get item by ID

**Response Format:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "prod_01",
      "name": "Product Name",
      "price": 100,
      "category": "Books",
      "stock_quantity": 50,
      "description": "...",
      "rating": 4.5
    }
  ],
  "message": null
}
```

#### **4.2 Cart Service Lambda**

**File:** `cart_service.py`

**Handler:** `cart_service.lambda_handler`

**Triggers:**
- GET /cart
- POST /cart/add
- DELETE /cart/remove/{id}
- DELETE /cart

**Functions:**
1. **GET /cart** → Returns user's current cart items
2. **POST /cart/add** → Adds product (validates stock availability)
3. **DELETE /cart/remove/{id}** → Removes specific item
4. **DELETE /cart** → Clears entire cart

**Validation:**
- Check product exists in products_table_guru
- Validate stock_quantity > 0
- Prevent overselling

**Database Operations:**
- Read from `products_table_guru` (stock check)
- Read/write `cart_table_guru` (user_id: "user1")

#### **4.3 Order Service Lambda**

**File:** `order_service.py`

**Handler:** `order_service.lambda_handler`

**Triggers:**
- GET /order
- POST /order
- GET /order/{id}
- PUT /order/{id}

**Functions:**
1. **GET /order** → Returns all orders for user
2. **POST /order** → Creates order from cart items
   - Fetches cart
   - Validates all items exist
   - Aggregates duplicate items (sum quantities)
   - Generates UUID for order_id
   - Saves to orders_table_guru
   - **Publishes to SNS** (order-notifications-guru)
   - **Sends to SQS** (order-processing-queue-guru)
   - Clears cart
3. **GET /order/{id}** → Returns specific order details
4. **PUT /order/{id}** → Updates order status

**Database Operations:**
- Read `cart_table_guru`
- Read `products_table_guru` (validation)
- Write `orders_table_guru`

**Messaging Integration:**
- **SNS:** Publishes notification when order created
- **SQS:** Sends order data to queue for async processing

**Order Schema:**
```json
{
  "order_id": "uuid-string",
  "items": [
    {
      "id": "prod_01",
      "name": "Product",
      "price": 100,
      "quantity": 2
    }
  ],
  "status": "created|processing|paid",
  "timestamp": "2025-04-15T10:00:00Z"
}
```

#### **4.4 Payment Service Lambda**

**File:** `payment_service.py`

**Handler:** `payment_service.lambda_handler`

**Triggers:**
- POST /payment

**Functions:**
1. **POST /payment**
   - Receives: `{order_id, amount}`
   - Fetches order from DynamoDB
   - Validates amount matches order total
   - **Simulates payment:** 50% success, 50% failure (random)
   - If success: Updates order status to "paid"
   - **Publishes to SNS:** Payment notification (success/failure)
   - Returns payment confirmation

**Database Operations:**
- Read `orders_table_guru` (fetch order)
- Update `orders_table_guru` (status → "paid")

**Messaging Integration:**
- **SNS:** Publishes payment result notification

**Payment Response:**
```json
{
  "status": "success",
  "data": {
    "payment_id": "uuid",
    "order_id": "uuid",
    "amount": 500,
    "status": "success|failed"
  },
  "message": "Payment successful|Payment failed"
}
```

#### **4.5 Search Service Lambda**

**File:** `search_service.py`

**Handler:** `search_service.lambda_handler`

**Triggers:**
- GET /search?q=query

**Functions:**
1. **GET /search**
   - Query parameter: `q` (search query)
   - Performs table scan on `products_table_guru`
   - Case-insensitive search on name + description
   - Returns matching products

**Database Operations:**
- Scan `products_table_guru` (all items)
- Client-side filtering (name/description match)

#### **4.6 Order Processor Lambda**

**File:** `order_processor.py`

**Handler:** `order_processor.lambda_handler`

**Triggers:**
- **SQS Messages** from order-processing-queue-guru
- **Event Source Mapping:** Polls queue every N seconds, batch size: 1

**Functions:**
1. **Process Order Message**
   - Receive order from SQS
   - Fetch order from DynamoDB
   - Update order status to "processing"
   - Delete message from queue
   - Ready for additional logic (email, inventory, etc.)

**Database Operations:**
- Read/update `orders_table_guru`

**Message Processing:**
```
SQS Queue polls every N seconds
    ↓
1 message received
    ↓
Lambda processes: Update order status
    ↓
Message deleted from queue
    ↓
Lambda waits for next message
```

**AWS Console Navigation:**

1. **View Lambda Functions:**
   - AWS Console → Lambda → Functions
   - Search for function name (e.g., "order_service_guru")
   - Click to open function detail

2. **View Function Configuration:**
   - Click function → Configuration tab
   - **General:** Memory (128 MB), Timeout (30s), Runtime (Python 3.12)
   - **Permissions:** Execution role (lambda_exec_role)
   - **Environment variables:** (None in this setup - using STS for account ID)
   - **VPC:** None (Lambda has internet access)

3. **View Function Code:**
   - Click function → Code tab
   - See Python source code
   - Edit inline or upload new zip

4. **Monitor Lambda Invocations:**
   - Click function → Monitor tab
   - **Invocations:** Total number of executions
   - **Errors:** Number of failed executions
   - **Duration:** Average execution time in ms
   - **Throttles:** How many times Lambda rate limit was hit
   - **Concurrent executions:** Running at same time

5. **View CloudWatch Logs:**
   - Click function → Monitor tab
   - "View CloudWatch Logs" link
   - OR go directly to CloudWatch → Log Groups
   - Log group name: `/aws/lambda/[function-name]`
   - See all print statements, errors, stack traces

6. **Test Lambda Function:**
   - Click function → Test tab
   - Create test event with sample payload
   - Click "Invoke" to test
   - See response and execution logs

7. **Monitor SQS Event Source:**
   - Click function → Configuration tab
   - **Triggers:** See "SQS" trigger for order_processor
   - Click SQS trigger to see:
     - Queue name
     - Batch size
     - State (enabled/disabled)
     - Last processing result

---

### 5. DYNAMODB (Database Layer)

**Purpose:** NoSQL database storing all application data. On-demand pricing model (pay per request).

**Billing Model:** Pay-Per-Request (no capacity planning needed)

#### **Table 1: products_table_guru**

**Hash Key:** id (String)

**Items:** 12 products (seeded on first call to product_service)

**Schema:**
```json
{
  "id": "prod_01",
  "name": "The Great Gatsby",
  "price": 2000,
  "category": "Books",
  "stock_quantity": 100,
  "description": "Classic novel by F. Scott Fitzgerald",
  "rating": 4.8
}
```

**Access Patterns:**
- Get all products (scan)
- Get product by ID (get item)
- Search by name (scan + filter)

#### **Table 2: cart_table_guru**

**Hash Key:** user_id (String)

**User:** "user1" (single user model for this MVP)

**Schema:**
```json
{
  "user_id": "user1",
  "cart": [
    {"id": "prod_01", "name": "Book", "price": 2000},
    {"id": "prod_02", "name": "Laptop", "price": 50000},
    {"id": "prod_01", "name": "Book", "price": 2000}  // Same item added twice
  ]
}
```

**Access Patterns:**
- Get cart (read)
- Add item (append to array)
- Remove item (filter array)
- Clear cart (set empty array)

#### **Table 3: orders_table_guru**

**Hash Key:** order_id (String, UUID)

**Schema:**
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "items": [
    {"id": "prod_01", "name": "Book", "price": 2000, "quantity": 2},
    {"id": "prod_02", "name": "Laptop", "price": 50000, "quantity": 1}
  ],
  "status": "created",
  "total": 54000,
  "timestamp": "2025-04-15T10:30:00Z"
}
```

**Access Patterns:**
- Get all orders (scan)
- Get order by ID (get item)
- Update order status

**AWS Console Navigation:**

1. **View DynamoDB Tables:**
   - AWS Console → DynamoDB → Tables
   - See 3 tables: products_table_guru, cart_table_guru, orders_table_guru

2. **Explore Table Items:**
   - Click table → Explore items
   - See all items in table
   - Click item to view/edit details
   - Add/delete items manually

3. **Check Table Metrics:**
   - Click table → Metrics tab
   - **Consumed Read/Write Capacity:** Usage over time
   - **User Errors:** Count of validation errors
   - **System Errors:** Count of AWS errors

4. **Monitor Table Performance:**
   - CloudWatch → Namespaces → AWS/DynamoDB
   - Select metric (ConsumedWriteCapacityUnits, etc.)
   - Create custom metrics for specific tables

5. **Setup Backups:**
   - Click table → Backups tab
   - Create on-demand backup (for disaster recovery)
   - Point-in-time recovery settings

---

### 6. SNS (Simple Notification Service)

**Purpose:** Publish order and payment notifications. Currently subscribed to SQS for async processing.

**Topic Name:** order-notifications-guru

**Type:** Standard Topic (FIFO not needed)

**When Notifications Are Published:**
1. Order created (from order_service)
2. Payment successful/failed (from payment_service)

**Subscribers:**
- **SQS Queue** (order-processing-queue-guru) - Primary subscriber for processing
- **Email** (guruprasad.reddy@idp.com) - User notifications

**Message Format:**
```json
{
  "Subject": "New Order Created: [order_id]",
  "Message": "Order [order_id] has been created with N items."
}
```

**How It Works:**
```
Publisher (Lambda)
    ↓
SNS Topic (order-notifications-guru)
    ├─ Email → User receives notification
    └─ SQS → Order Processor Lambda
```

**AWS Console Navigation:**

1. **View SNS Topic:**
   - AWS Console → SNS → Topics
   - Click "order-notifications-guru"

2. **Topic Overview:**
   - Topic Details tab
   - See Topic ARN (arn:aws:sns:ap-southeast-1:ACCOUNT_ID:order-notifications-guru)
   - See number of subscriptions

3. **View Subscriptions:**
   - Subscriptions tab
   - See SQS queue subscription details
   - Filter, edit, or delete subscriptions

4. **Monitor Published Messages:**
   - Click topic → Monitoring tab
   - **NumberOfMessagesPublished:** Total messages sent
   - **NumberOfNotificationsFailed:** Failed deliveries
   - Create alarms for failures

5. **Test Publishing (Manual):**
   - Click topic → Publish message
   - Enter subject and message
   - Click Publish
   - Message routes to SQS subscribers

---

### 7. SQS (Simple Queue Service)

**Purpose:** Store order messages asynchronously. Order Processor Lambda consumes messages.

**Queue Type:** Standard (FIFO not needed, ordering not critical)

#### **Main Queue: order-processing-queue-guru**

**Configuration:**
- Visibility Timeout: 300 seconds (5 minutes)
- Message Retention: 345,600 seconds (4 days)
- Receive Message Wait Time: 0 (short polling)
- Dead Letter Queue: Yes, enabled

**Message Example:**
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "items": [
    {"id": "prod_01", "name": "Book", "price": 2000, "quantity": 2}
  ],
  "status": "created"
}
```

**Message Lifecycle:**
```
SNS publishes message
    ↓
Message appears in queue (Available)
    ↓
Order Processor Lambda polls queue
    ↓
Message delivered to Lambda (In Flight, hidden for 5 minutes)
    ↓
Lambda processes order
    ↓
Lambda deletes message from queue
    ↓
Message removed
```

#### **Dead Letter Queue: order-processing-queue-guru-dlq**

**Purpose:** Capture failed messages (failures after 5 retries)

**When Messages Move to DLQ:**
- Lambda throws unhandled exception
- Message fails 5 times (configurable)
- Message moves to DLQ automatically

**Debugging DLQ:**
- View failed orders still in queue
- Check logs for error reasons
- Manually handle failed orders

**AWS Console Navigation:**

1. **View SQS Queues:**
   - AWS Console → SQS → Queues
   - See "order-processing-queue-guru" and "order-processing-queue-guru-dlq"

2. **Queue Overview:**
   - Click queue → Details tab
   - Queue URL
   - Queue ARN
   - Visibility timeout (300s)
   - Message retention (4 days)
   - Redrive (DLQ settings)

3. **Monitor Queue Metrics:**
   - Click queue → Monitoring tab
   - **NumberOfMessagesSent:** Messages published to queue
   - **NumberOfMessagesReceived:** Messages consumed
   - **NumberOfMessagesDeleted:** Successfully processed
   - **ApproximateNumberOfMessagesVisible:** Pending messages
   - **ApproximateNumberOfMessagesNotVisible:** In-flight messages
   - **ApproximateAgeOfOldestMessage:** Oldest message age

4. **Send/Receive Messages (Manual):**
   - Click queue → Send and receive messages
   - Send → Enter message body → Publish
   - Receive → Poll for messages → See in queue

5. **View Messages in Queue:**
   - Click queue → Send and receive messages
   - Receive message → See message body
   - Message stays for visibility timeout (5 min) then gets retried
   - Delete message manually when inspected

6. **Purge Queue (Dangerous):**
   - Click queue → delete-queue or Purge settings
   - Removes ALL messages instantly
   - Use only for testing/cleanup

---

### 8. IAM (Identity & Access Management)

**Purpose:** Control permissions for Lambda functions to access other AWS services.

#### **Lambda Execution Role: lambda_exec_role_guru**

**Trust Relationship:** Lambda service can assume this role

**Attached Policies:**
1. **AWSLambdaBasicExecutionRole** (AWS Managed)
   - Permission: Write logs to CloudWatch
   - Action: `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`
   - Resource: `/aws/lambda/*`

2. **AmazonDynamoDBFullAccess** (AWS Managed)
   - Permission: Full DynamoDB access
   - Actions: `dynamodb:*`
   - Resource: All DynamoDB tables

3. **AmazonSQSFullAccess** (AWS Managed)
   - Permission: Full SQS access
   - Actions: `sqs:*` (SendMessage, ReceiveMessage, DeleteMessage)
   - Resource: SQS queues

4. **AmazonSNSFullAccess** (AWS Managed)
   - Permission: Full SNS access
   - Actions: `sns:*` (Publish)
   - Resource: SNS topics

**AWS Console Navigation:**

1. **View Lambda Role:**
   - AWS Console → IAM → Roles
   - Search "lambda_exec_role"

2. **Trust Relationships:**
   - Click role → Trust relationships tab
   - See principal: `"Service": "lambda.amazonaws.com"`
   - Lambda service can assume this role

3. **View Attached Policies:**
   - Click role → Permissions tab
   - See all 4 attached policies
   - Click policy to view permissions

4. **Analyze Role Permissions:**
   - AWS Access Analyzer → Analyze role
   - See if permissions are externally accessible
   - Check for overly permissive policies

---

## Data Flow Examples

### Scenario 1: User Places Order

```
┌─── FRONTEND ──────────────────────────────────────────┐
│ User clicks "Place Order"                             │
│ React state: cart = [{id: "prod_01", ...}, ...]     │
└────────────────┬────────────────────────────────────┘
                 │ HTTP POST /order
                 │ Body: {items: [{id: "prod_01"}, ...]}
                 ↓
┌─── API GATEWAY ────────────────────────────────────┐
│ Route: POST /order                                 │
│ Rate limit check: OK (< 50 RPS)                   │
│ CORS headers added                                 │
│ Throttle: 100 RPS burst available                 │
└────────────────┬────────────────────────────────┘
                 │ Invoke Lambda
                 ↓
┌─── ORDER SERVICE LAMBDA ──────────────────────────┐
│ 1. Parse request body                             │
│ 2. Fetch cart from DynamoDB (cart_table_guru)    │
│    Key: {user_id: "user1"}                       │
│ 3. Validate items                                 │
│    FOR each item in request:                     │
│      - Fetch product from products_table_guru    │
│      - Check if in cart                          │
│      - Check quantity after aggregation          │
│ 4. Aggregate items (sum duplicate quantities)     │
│    [{id: "prod_01", qty: 1}, {id: "prod_01"}]   │
│    → [{id: "prod_01", qty: 2}]                  │
│ 5. Create order object                           │
│    {order_id: UUID, items: [...], status: "..."}│
│ 6. Save to DynamoDB                              │
│    Put item: orders_table_guru                   │
│ 7. PUBLISH TO SNS                                │
│    Topic: order-notifications-guru               │
│    Message: {order_id, items_count, ...}         │
│ 8. SEND TO SQS                                   │
│    Queue: order-processing-queue-guru            │
│    Message body: full order JSON                 │
│ 9. Clear cart in DynamoDB                        │
│    Update: cart_table_guru                       │
│    Set cart: []                                  │
│ 10. Return response to API Gateway               │
└────────────────┬────────────────────────────────┘
                 │ HTTP 200 OK
                 │ Body: {status: "success", data: {...}}
                 ↓
┌─── API GATEWAY ────────────────────────────────┐
│ Add CORS headers                               │
│ Return response to client                      │
└────────────────┬────────────────────────────┘
                 │ HTTP 200 OK
                 ↓
┌─── FRONTEND ────────────────────────────────┐
│ Response received                           │
│ Update state: cart = []                    │
│ Navigate to orders view                    │
│ Show success message                       │
└────────────────────────────────────────────┘

┌─── BACKGROUND: SNS → EMAIL + SQS ──────────────────────┐
│ SNS receives order message                           │
│ Routes to all subscribers:                           │
│ ├─ Email → guruprasad.reddy@idp.com receives alert  │
│ └─ SQS Queue → Message appears in queue (Available) │
│                                                     │
│ Order Processor Lambda polls SQS                    │
│ Receives message (In Flight, 5 min timeout)         │
│ Processes: Updates order status → "processing"      │
│ Updates: orders_table_guru                          │
│ Deletes message from queue                          │
│ Ready for next message                              │
└─────────────────────────────────────────────────────┘
```

**AWS Console Path to Track:**

1. **See Order in DynamoDB:**
   - DynamoDB → Tables → orders_table_guru → Explore items
   - New order appears here

2. **See Message in Queue:**
   - SQS → Queues → order-processing-queue-guru
   - "Send and receive messages" → Poll for messages
   - See order JSON in queue (briefly, until processed)

3. **See Lambda Invocations:**
   - Lambda → Functions → order_service_guru → Monitor
   - Invocation count increments
   - Duration shows execution time

4. **See CloudWatch Logs:**
   - CloudWatch → Log Groups → /aws/lambda/order_service_guru/
   - See "Order {order_id} created" logs
   - See SQS send confirmation

5. **See SNS Publication:**
   - SNS → Topics → order-notifications-guru → Monitoring
   - NumberOfMessagesPublished increments

---

### Scenario 2: User Makes Payment

```
┌─── FRONTEND ────────────────────────────┐
│ User views orders                       │
│ Clicks "Pay" on order                   │
│ Order visible: order_id = "uuid123"    │
└────────────────┬─────────────────────┘
                 │ HTTP POST /payment
                 │ Body: {order_id: "uuid123", amount: 54000}
                 ↓
┌─── API GATEWAY ─────────────────────┐
│ Route: POST /payment               │
│ CORS check: OK                      │
│ Rate limit: OK                      │
└────────────────┬───────────────────┘
                 │ Invoke Lambda
                 ↓
┌─── PAYMENT SERVICE LAMBDA ──────────────────┐
│ 1. Parse request                            │
│    order_id = "uuid123"                     │
│    amount = 54000                           │
│ 2. Fetch order from DynamoDB                │
│    Key: {order_id: "uuid123"}              │
│    Item: {items: [...], total: 54000}      │
│ 3. Validate amount matches total            │
│    Received: 54000                          │
│    Actual: 54000                            │
│    Match: YES ✓                             │
│ 4. Simulate payment (50/50 random)          │
│    Random = True (success)                  │
│ 5. Update order status                      │
│    UpdateExpression: SET status = "paid"   │
│    Update: orders_table_guru                │
│ 6. PUBLISH TO SNS                          │
│    Topic: order-notifications-guru          │
│    Subject: "Payment Success: Order uuid123"│
│    Message: "Payment received"              │
│ 7. Return response                          │
│    {status: "success", data: {...}}        │
└────────────────┬──────────────────────┘
                 │ HTTP 200 OK
                 ↓
┌─── FRONTEND ────────────────────┐
│ Response received               │
│ Show success alert              │
│ Update order status to "paid"  │
│ Refresh order view              │
└────────────────────────────────┘

┌─── BACKGROUND: SNS → EMAIL + SQS ──────────────────┐
│ SNS routes payment notification to all subscribers: │
│ ├─ Email → guruprasad.reddy@idp.com receives alert │
│ └─ SQS → Order Processor receives message         │
│ Already processed (status already updated)        │
│ (Order Processor just marks as "processing")      │
└────────────────────────────────────────────────────┘
```

**AWS Console Path to Track:**

1. **See Updated Order:**
   - DynamoDB → Tables → orders_table_guru
   - Click order_id → See status = "paid"

2. **See Payment Logs:**
   - Lambda → Functions → payment_service_guru → Monitor
   - Click "View logs in CloudWatch"
   - See payment processing logs

3. **See SNS Notification:**
   - SNS → Topics → order-notifications-guru → Monitoring
   - Message count increases

---

## AWS Console Navigation

### Quick Reference: Where to Find Everything

| What You Want to Check | AWS Service | Path |
|------------------------|-------------|------|
| **Frontend is live** | CloudFront | Distributions → Click domain |
| **Frontend files in cache** | S3 | Buckets → ecommerce-frontend-guru → Objects |
| **API requests** | API Gateway | APIs → API_Services_Guru → Routes |
| **API errors** | CloudWatch | Log Groups → /aws/api-gateway/... |
| **Lambda execution** | Lambda | Functions → [function-name] → Monitor |
| **Lambda code** | Lambda | Functions → [function-name] → Code |
| **Lambda logs** | CloudWatch | Log Groups → /aws/lambda/[function-name]/ |
| **Database data** | DynamoDB | Tables → [table-name] → Explore items |
| **Database metrics** | DynamoDB | Tables → [table-name] → Metrics |
| **Queue messages** | SQS | Queues → [queue-name] → Send and Receive |
| **Queue metrics** | SQS | Queues → [queue-name] → Monitoring |
| **Topic messages** | SNS | Topics → [topic-name] → Monitoring |
| **IAM permissions** | IAM | Roles → lambda_exec_role_guru |

---

## Monitoring & Metrics

### Key Metrics to Monitor

#### CloudWatch Metrics to Watch

```
Lambda Metrics:
  - Invocations: Normal operation (should correlate with API calls)
  - Errors: Should be low or zero
  - Duration: Should be consistent (< 5 seconds usually)
  - Throttles: Should be zero (if non-zero, increase concurrency)
  - ConcurrentExecutions: Typical workload level

DynamoDB Metrics:
  - ConsumedWriteCapacityUnits: Write operations
  - ConsumedReadCapacityUnits: Read operations
  - UserErrors: Validation/business logic errors
  - SystemErrors: AWS infrastructure errors

SQS Metrics:
  - NumberOfMessagesSent: Messages published to queue
  - NumberOfMessagesReceived: Messages consumed by Lambda
  - ApproximateNumberOfMessagesVisible: Pending messages
  - ApproximateAgeOfOldestMessage: How long oldest message waiting

API Gateway Metrics:
  - Count: Total API requests
  - 4xx: Client errors (bad requests)
  - 5xx: Server errors (Lambda failures)
  - Latency: Response time in milliseconds

CloudFront Metrics:
  - Requests: Total requests to CDN
  - BytesDownloaded: Data sent to users
  - CacheHitRate: Percentage of requests served from cache
```

### Create CloudWatch Dashboard

**Steps:**
1. CloudWatch → Dashboards → Create dashboard
2. Add widgets:
   - Lambda invocations (all functions)
   - Lambda errors (all functions)
   - SQS messages available
   - SQS messages processed
   - DynamoDB write capacity
   - API Gateway errors
---

## Testing Guide

### Unit Testing Suite

**Framework:** pytest with moto (AWS service mocking)

**Test Coverage:** 35 comprehensive tests across all services

**Run Tests:**
```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Run all tests
python run_tests.py

# Or run specific test file
pytest tests/test_product_service.py -v
```

**Test Files:**
- `tests/test_product_service.py` - 5 tests (CRUD operations, seeding, error handling)
- `tests/test_cart_service.py` - 8 tests (cart management, stock validation)
- `tests/test_order_service.py` - 7 tests (order creation, validation, status updates)
- `tests/test_payment_service.py` - 7 tests (payment processing, error scenarios)
- `tests/test_search_service.py` - 8 tests (search functionality, case sensitivity)

**Test Results Summary:**
```
Test Summary: 35 passed, 0 failed
├── Product Service: 5/5 ✅
├── Cart Service: 8/8 ✅
├── Order Service: 7/7 ✅
├── Payment Service: 7/7 ✅
└── Search Service: 8/8 ✅
```

**Mocking Strategy:**
- **DynamoDB Tables:** Mocked with moto for isolated testing
- **SQS Queues:** Mocked message sending/receiving
- **SNS Topics:** Mocked notification publishing
- **Environment Variables:** AWS region and credentials mocked

### End-to-End Testing Workflow

#### **Setup: Open Multiple AWS Console Tabs**

1. Tab 1: CloudWatch Logs
2. Tab 2: SQS Queue
3. Tab 3: DynamoDB Tables
4. Tab 4: Lambda Functions
5. Tab 5: CloudWatch Metrics

#### **Test Scenario: Create Order → Process → Pay**

**Step 1: Clear Previous State**
```
1. SQS → order-processing-queue-guru → Purge messages (optional)
2. DynamoDB → cart_table_guru → Delete user1 item (to start fresh)
```

**Step 2: Place Order**
```
1. Frontend → Add product to cart
2. Watch CloudWatch Logs:
   - /aws/lambda/cart_service_guru → See "Item added to cart"
3. Frontend → View cart → Click "Place Order"
4. Watch CloudWatch Logs:
   - /aws/lambda/order_service_guru → See order created
   - See SQS send confirmation
5. DynamoDB → orders_table_guru → New order appears
6. SQS → Poll queue → See order message (may disappear if processed)
```

**Step 3: Order Processing**
```
1. Lambda → Functions → order_processor_guru → Monitor
   - See invocation count increase
   - See duration (processing time)
2. CloudWatch Logs:
   - /aws/lambda/order_processor_guru → See "Order X status updated"
3. DynamoDB → orders_table_guru → Order status = "processing"
```

**Step 4: Make Payment**
```
1. Frontend → Orders → Click "Pay" on order
2. CloudWatch Logs:
   - /aws/lambda/payment_service_guru → See payment result
3. DynamoDB → orders_table_guru → Order status = "paid" or "created"
4. SNS → Topics → order-notifications-guru → Monitoring
   - Message count increases
```

#### **Verify Each Component**

| Component | How to Verify | Expected Result |
|-----------|---------------|-----------------|
| Frontend | Open CloudFront domain | React app loads, no errors |
| CloudFront Cache | Hard refresh (Ctrl+Shift+R) | Page loads from CDN |
| API Gateway | Place order → See order ID in response | Success response (200) |
| Order Service | CloudWatch logs | "Order created" message |
| DynamoDB | Explore items | New order visible |
| SNS | Topic monitoring | Message count increased |
| SQS | Poll queue | Message JSON displayed |
| Order Processor | Lambda monitor | Status updated in DynamoDB |

---

## API Documentation

### OpenAPI Specification

**File:** `openapi-spec.json`

**Features:**
- Complete API documentation for all 12 endpoints
- Request/response schemas with examples
- Authentication configuration (Bearer token)
- Error response definitions
- Interactive testing via Swagger UI

**API Endpoints Summary:**

| Method | Endpoint | Description | Service |
|--------|----------|-------------|---------|
| GET | `/v1/products` | List all products | Product Service |
| GET | `/v1/products/{id}` | Get product details | Product Service |
| GET | `/v1/search?q={query}` | Search products | Search Service |
| GET | `/v1/cart` | Get shopping cart | Cart Service |
| POST | `/v1/cart/add` | Add item to cart | Cart Service |
| DELETE | `/v1/cart/remove/{id}` | Remove item from cart | Cart Service |
| DELETE | `/v1/cart` | Clear entire cart | Cart Service |
| GET | `/v1/order` | Get order history | Order Service |
| POST | `/v1/order` | Create new order | Order Service |
| GET | `/v1/order/{id}` | Get order details | Order Service |
| PUT | `/v1/order/{id}` | Update order status | Order Service |
| POST | `/v1/payment` | Process payment | Payment Service |

### Response Format Standards

**Success Response:**
```json
{
  "status": "success",
  "data": { ... },
  "message": null
}
```

**Error Response:**
```json
{
  "status": "error",
  "data": null,
  "message": "Error description"
}
```

### Authentication

**Type:** Bearer Token (JWT)
**Header:** `Authorization: Bearer {token}`
**Configuration:** Defined in OpenAPI security schemes

### Testing the API

**Method 1: Swagger UI**
1. Open `openapi-spec.json` in a Swagger viewer
2. Configure authentication if required
3. Test endpoints interactively

**Method 2: Direct API Calls**
```bash
# Example: Get all products
curl -X GET "https://[api-id].execute-api.[region].amazonaws.com/v1/products"

# Example: Search products
curl -X GET "https://[api-id].execute-api.[region].amazonaws.com/v1/search?q=laptop"
```

**Method 3: Postman/Insomnia**
- Import `openapi-spec.json`
- Configure base URL and authentication
- Test all endpoints

---

## Troubleshooting

### Common Issues & Solutions

#### **Issue: API returns "Route not found" for /v1/* endpoints**

**Cause:** Lambda handlers not updated for versioned paths

**Solution:**
1. Check Lambda handler code:
   - Each service should have: `if path.startswith("/v1/"): path = path[3:]`
   - This strips the `/v1` prefix before route matching
2. Verify API Gateway stage:
   - API Gateway → APIs → API_Services_Guru → Stages → v1
   - Stage should be deployed and active
3. Test both paths:
   - `/products` and `/v1/products` should work identically
   - Check CloudWatch logs for path processing

#### **Issue: Frontend shows "Connection Refused" or "Cannot reach API"**

**Cause:** API Gateway endpoint not accessible

**Solution:**
1. Check API Gateway is deployed:
   - API Gateway → APIs → API_Services_Guru
   - Stages → *$default → Check if "Deployed"
2. Check CloudFront origins:
   - CloudFront → Distributions → Click distribution
   - Origins tab → API Gateway origin health
3. Check frontend API_BASE URL:
   - frontend/src/App.js → Line with API_BASE
   - Should be CloudFront domain or API Gateway domain

#### **Issue: Order placed but doesn't appear in DynamoDB**

**Cause:** Order Service Lambda failed

**Solution:**
1. Check Lambda logs:
   - Lambda → Functions → order_service_guru → Monitor
   - View logs in CloudWatch
   - Look for error messages
2. Check Lambda permissions:
   - Lambda → order_service_guru → Configuration → Permissions
   - Ensure lambda_exec_role has DynamoDB access
3. Check DynamoDB table exists:
   - DynamoDB → Tables → orders_table_guru
   - Verify table created successfully

#### **Issue: Messages stuck in SQS queue (not being processed)**

**Cause:** Order Processor Lambda not triggered or failing

**Solution:**
1. Check event source mapping:
   - Lambda → Functions → order_processor_guru
   - Configuration → Triggers → SQS trigger
   - Verify state is "Enabled"
2. Check Lambda logs:
   - /aws/lambda/order_processor_guru
   - Look for errors in message processing
3. Check queue visibility:
   - SQS → Queues → order-processing-queue-guru
   - Visibility timeout may be too long
   - Reduce timeout to 30 seconds for testing

#### **Issue: Payment always fails (50% random)**

**Cause:** Random failure in payment_service (by design)

**Solution:**
1. This is intentional - payment is simulated randomly
2. To test both paths: Try payment multiple times
3. To always succeed: Modify payment_service.py:
   - Change: `payment_success = random.choice([True, False])`
   - To: `payment_success = True`
   - Repackage and redeploy

#### **Issue: High Lambda costs**

**Cause:** Excessive invocations or long duration

**Solution:**
1. Monitor actual usage:
   - Lambda → Functions → Each function → Monitor
   - Check duration and invocation count
2. Optimize code:
   - Reduce DynamoDB queries
   - Cache frequently accessed data
   - Use batch operations
3. Check for loops:
   - Search for repeated API calls in Lambda code
   - Combine multiple operations

#### **Issue: DynamoDB "Throughput limit exceeded"**

**Cause:** Too many operations on pay-per-request table (shouldn't happen)

**Solution:**
1. Check for runaway scans:
   - Search service scans entire table
   - Consider adding Global Secondary Index (GSI)
2. Check for throttling:
   - DynamoDB → Tables → Metrics
   - Look for UserErrors or system throttles
3. If critical:
   - Switch to provisioned capacity
   - Set high WCU/RCU limits

---

## Observability Implementation Guide

### When You Have AWS Monitoring Permissions

If you have appropriate AWS permissions, you can implement comprehensive observability using this Terraform configuration:

#### **monitoring.tf** (Add this file when ready)

```hcl
# CloudWatch Alarms
resource "aws_cloudwatch_alarm" "lambda_errors" {
  alarm_name          = "MyStore-Lambda-Errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1"
  
  alarm_actions = [aws_sns_topic.alerts.arn]
}

# CloudWatch Logs
resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/lambda/mystore-api"
  retention_in_days = 30
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "mystore_dashboard" {
  dashboard_name = "MyStore-Dashboard"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        properties = {
          metrics = [["AWS/ApiGateway", "Count", "ApiName", "mystore-api"]]
          title   = "API Gateway Requests"
        }
      }
    ]
  })
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "mystore-alerts"
}

# Optional: X-Ray Tracing
resource "aws_xray_sampling_rule" "mystore_sampling" {
  rule_name      = "MyStore-Sampling"
  priority       = 10
  reservoir_size = 1
  fixed_rate     = 0.05
  url_path       = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = "*"
  host           = "*"
}
```

#### **Required AWS Permissions for Observability**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:*",
        "logs:*",
        "sns:*",
        "xray:*"
      ],
      "Resource": "*"
    }
  ]
}
```

#### **Key Metrics to Monitor**

- **Lambda**: Invocations, Errors, Duration, Throttles
- **API Gateway**: Request Count, 4xx/5xx Errors, Latency
- **DynamoDB**: Consumed Capacity, User/System Errors
- **SQS**: Messages Sent/Received, Queue Depth, Age of Oldest Message

#### **Setting Up Alerts**

1. **Lambda Errors**: Alert when any Lambda function fails
2. **API 5xx Errors**: Alert on server-side errors
3. **Queue Depth**: Alert when messages pile up in SQS
4. **High Latency**: Alert when API response time exceeds threshold

---

## Architecture Decision Log

### Why Serverless?

- **No server management** required
- **Auto-scaling** built-in
- **Pay for what you use** (no idle servers)
- **Built-in reliability** (AWS manages infrastructure)

### Why DynamoDB?

- **Scales automatically** with pay-per-request billing
- **Single-digit millisecond** latency
- **Built-in replication** across AZs
- **No SQL expertise needed** for this use case

### Why SQS + SNS?

- **Decouples order creation** from order processing
- **Guarantees message delivery** (DLQ for failures)
- **Enables async workflows** (order processor doesn't block user)
- **Easy to add subscribers** (email, SMS, webhooks later)

### Why CloudFront + S3?

- **Global CDN** for fast frontend delivery
- **Origin Access Identity** keeps S3 private/secure
- **Built-in cache invalidation** for updates
- **Integrated with API Gateway** for single distribution

---

## Future Enhancements

1. **Multi-User Support:** Add authentication (Cognito), separate carts per user
2. **Real Payments:** Integrate Stripe/PayPal instead of random simulation
3. **Search Optimization:** Add DynamoDB Global Secondary Index for efficient search
4. **Analytics:** Send metrics to Amazon QuickSight dashboard
5. **Admin Dashboard:** Lambda + API for viewing all orders/payments
6. **Inventory Management:** Real inventory deduction in Lambda
7. **Order Tracking:** Add order status history and events
8. **SMS Notifications:** Add SMS subscription to SNS for mobile alerts

---

**Last Updated:** April 20, 2026  
**Version:** 1.2  
**Status:** Production Ready with API Versioning
