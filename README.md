# MyStore E-commerce Platform

A full-stack serverless e-commerce platform built with React, AWS Lambda, DynamoDB, and Auth0.

## 🚀 Features

- **Product Catalog** - Browse, search, and filter products with pagination
- **Product Variants** - Size, color, and capacity options for products
- **Shopping Cart** - Add/remove items with automatic cart management
- **Wishlist** - Save favorite products for later
- **User Authentication** - Secure Auth0 JWT-based authentication
- **Order Management** - Create orders with address validation and order tracking
- **Payment Processing** - Razorpay integration with fallback simulation mode
- **Product Reviews** - Rate and review products (verified purchase only)
- **Return Management** - Request, approve, reject, and refund returns
- **Admin Panel** - Manage products, orders, returns, and inventory with analytics dashboard
- **Email Notifications** - Transactional emails via Gmail SMTP (verified users only)
- **Order History Filters** - Filter orders by status, date range, and sort order
- **Email Verification Reminders** - Banner and checkout warning for unverified users

## 🛠️ Tech Stack

### Frontend
- **React 18** - UI framework
- **React Router v7** - Client-side routing
- **Auth0 React SDK** - Authentication
- **CSS3** - Styling (no framework dependencies)

### Backend
- **AWS Lambda** - Serverless compute (Python 3.12)
- **API Gateway HTTP API** - RESTful API with JWT authorizer
- **DynamoDB** - NoSQL database with GSI for efficient queries
- **SQS** - Asynchronous order processing queue
- **SNS** - Admin notifications via email

### Infrastructure
- **Terraform** - Infrastructure as Code
- **CloudFront** - CDN for frontend distribution
- **S3** - Static website hosting
- **IAM** - Fine-grained access control

### Third-Party Services
- **Auth0** - User authentication and authorization
- **Razorpay** - Payment gateway (Indian market)
- **Gmail SMTP** - Transactional email delivery (App Password, verified users only)

## 📋 Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.12+
- **Terraform** 1.0+
- **AWS CLI** configured with appropriate credentials
- **Auth0 account** with API configured
- **Razorpay account** (optional, falls back to simulation)
- **Gmail account** with App Password (optional, for email notifications)

## ⚡ Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Configure environment variables

Create `infrastructure/terraform.tfvars`:

```hcl
aws_region              = "ap-southeast-1"
aws_profile             = "your-aws-profile"
notification_email      = "your-email@example.com"
auth0_domain            = "your-tenant.auth0.com"
auth0_audience          = "https://api.mystore.com"
auth0_m2m_client_id     = "your-m2m-client-id"
auth0_m2m_client_secret = "your-m2m-client-secret"
razorpay_key_id         = "your-razorpay-key-id"
razorpay_key_secret     = "your-razorpay-key-secret"
smtp_user               = "yourstore@gmail.com"          # optional
smtp_password           = "xxxx xxxx xxxx xxxx"          # Gmail App Password
smtp_from               = "MyStore <yourstore@gmail.com>"
```

### 3. Deploy infrastructure

```bash
cd infrastructure
terraform init
terraform plan
terraform apply
```

Note the outputs:
- `api_url` - Your API Gateway endpoint
- `cloudfront_url` - Your frontend CDN URL
- `s3_bucket_name` - Frontend hosting bucket

### 4. Seed products

```bash
cd ../scripts
python seed_products.py
```

### 5. Build and deploy frontend

```bash
cd ../frontend
npm install
npm run build

# Deploy to S3 (PowerShell)
cd ../scripts
./deploy_frontend.ps1
```

### 6. Configure Auth0

1. Create an Auth0 Application (Single Page Application)
2. Set **Allowed Callback URLs**: `http://localhost:3000, https://your-cloudfront-url`
3. Set **Allowed Logout URLs**: `http://localhost:3000, https://your-cloudfront-url`
4. Set **Allowed Web Origins**: `http://localhost:3000, https://your-cloudfront-url`
5. Create an API with identifier: `https://api.mystore.com`
6. Create a **Post-Login Action** with the following code and add it to the Login flow:
   ```javascript
   exports.onExecutePostLogin = async (event, api) => {
     const ns = 'https://mystore.com/';
     api.accessToken.setCustomClaim(ns + 'email', event.user.email);
     api.accessToken.setCustomClaim(ns + 'email_verified', event.user.email_verified);
     api.accessToken.setCustomClaim(ns + 'roles', event.authorization?.roles || []);
   };
   ```
7. Update `frontend/src/index.js` with your Auth0 domain and client ID

### 7. Access the application

- **Production**: `https://your-cloudfront-url`
- **Local Development**: `npm start` (from frontend directory)

## 📁 Project Structure

```
.
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/      # React components (with component-scoped CSS)
│   │   ├── hooks/           # Custom React hooks
│   │   └── services/        # API service layer
│   └── public/              # Static assets
├── services/                # Lambda function handlers
│   ├── catalog_service.py   # Product catalog, search & reviews
│   ├── order_service.py     # Order management & returns
│   ├── payment_service.py   # Payment processing (Razorpay)
│   ├── user_service.py      # User profile, cart & wishlist
│   ├── admin_service.py     # Admin operations & analytics
│   ├── order_processor.py   # SQS order fulfillment
│   ├── utils.py             # Shared utilities (Gmail SMTP, SNS, order status, table names)
│   └── validation.py        # Input validation (no external dependencies)
├── infrastructure/          # Terraform IaC
│   ├── main.tf             # Provider configuration
│   ├── lambda.tf           # Lambda functions
│   ├── api.tf              # API Gateway routes
│   ├── api_versioning.tf   # Versioned API routes (v1)
│   ├── dynamodb.tf         # Database tables
│   ├── messaging.tf        # SQS & SNS
│   ├── frontend.tf         # S3 & CloudFront
│   └── iam.tf              # IAM roles & policies
├── scripts/                # Deployment & utility scripts
│   ├── build_lambdas.ps1   # Package Lambda functions (no dependencies)
│   ├── deploy_frontend.ps1 # Deploy frontend to S3
│   └── seed_products.py    # Seed initial product data
├── tests/                  # Test suites
└── docs/                   # Documentation
```

## 🔑 Key Endpoints

### Public Endpoints (No Auth Required)
- `GET /products` - List products with pagination
- `GET /products/{id}` - Get product details
- `GET /products/{id}/variants` - Get product variants
- `GET /products/{id}/reviews` - Get product reviews
- `GET /search` - Search products with filters
- `GET /recommendations` - Get product recommendations

### Protected Endpoints (Auth Required)
- `GET /cart` - Get cart contents
- `POST /cart/add` - Add item to cart
- `DELETE /cart/remove/{id}` - Remove item from cart
- `POST /order` - Create order
- `GET /order` - Get order history
- `POST /payment` - Process payment
- `GET /wishlist` - Get wishlist
- `POST /wishlist/add` - Add to wishlist
- `POST /products/{id}/reviews` - Submit product review (verified purchase only)
- `POST /return` - Create return request
- `GET /return/{id}` - Get return request details

### Admin Endpoints (Admin Role Required)
- `GET /admin/dashboard` - Get dashboard stats with analytics
- `GET /admin/products` - List all products
- `PUT /admin/products/{id}` - Update product
- `DELETE /admin/products/{id}` - Delete product
- `GET /admin/orders` - List all orders
- `PUT /admin/orders/{id}` - Update order status
- `GET /admin/returns` - List all return requests
- `PUT /admin/returns/{id}/approve` - Approve return request
- `PUT /admin/returns/{id}/reject` - Reject return request with reason
- `PUT /admin/returns/{id}/refund` - Process refund for approved return

See [API Documentation](docs/API.md) for complete API reference.

## 🧪 Testing

```bash
# Run all tests
python run_tests.py

# Run specific test file
python -m pytest tests/test_catalog_service.py -v
```

## 📊 Monitoring

- **CloudWatch Logs** - Lambda execution logs
- **CloudWatch Metrics** - API Gateway metrics, Lambda invocations
- **DynamoDB Metrics** - Read/write capacity, throttling
- **X-Ray** - Distributed tracing (if enabled)

## 🔒 Security

- **JWT Authentication** - Auth0-issued tokens with audience validation
- **HTTPS Only** - All API traffic encrypted via API Gateway
- **CORS** - Configured for frontend domain only
- **IAM Least Privilege** - Lambda functions have minimal required permissions
- **Input Validation** - All user inputs validated before processing
- **SQL Injection Protection** - DynamoDB NoSQL (no SQL injection risk)
- **Secrets Management** - Sensitive credentials stored in Terraform variables

## 🚀 Deployment

### Production Deployment Checklist

- [ ] Update Auth0 callback URLs with production domain
- [ ] Configure custom domain for API Gateway
- [ ] Enable CloudFront custom domain with SSL certificate
- [ ] Set up CloudWatch alarms for critical metrics
- [ ] Enable DynamoDB point-in-time recovery (already enabled)
- [ ] Configure backup retention policies
- [ ] Set up monitoring dashboards
- [ ] Test payment flow with real Razorpay credentials
- [ ] Configure Gmail App Password and verify SMTP sends
- [ ] Review and adjust Lambda memory/timeout settings
- [ ] Enable API Gateway access logging
- [ ] Set up WAF rules for API protection

## 📖 Documentation

- [API Reference](docs/API.md) - Complete API documentation
- [Architecture](docs/ARCHITECTURE.md) - System design and data flow
- [Database Schema](docs/DATABASE.md) - DynamoDB table structures
- [Setup Guide](docs/SETUP.md) - Detailed setup instructions
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment
- [Security](docs/SECURITY.md) - Security best practices
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and fixes

## 🔮 Future Work

### Observability
- **CloudWatch integration** — Enable API Gateway access logging and Lambda execution logs to `/aws/apigateway/` log groups. Add CloudWatch alarms for 4xx/5xx error rates and Lambda throttles.
- **X-Ray tracing** — Distributed tracing across Lambda functions to identify latency bottlenecks.
- **Custom metrics dashboard** — CloudWatch dashboard for order volume, payment success rate, and inventory alerts.

### Security
- **AWS WAF** — Attach a Web Application Firewall to the API Gateway stage for IP-based rate limiting, bot protection, and OWASP rule sets.
- **DynamoDB-based rate limiting** — Per-user request counters in DynamoDB as a WAF alternative for sensitive endpoints (`/payment`, `/order`).
- **SNS-based abuse alerts** — Publish to the existing SNS topic when a user exceeds a request threshold within a Lambda, without needing WAF or CloudWatch.

### Infrastructure
- **Lambda provisioned concurrency** — Eliminate cold starts on the catalog and payment services for consistent response times.
- **Multi-region deployment** — DynamoDB Global Tables + multi-region Lambda for disaster recovery and lower latency outside ap-southeast-1.

### Features
- **Order tracking page** — Real-time shipment tracking with carrier integration.
- **Discount codes and coupons** — Promo code validation at checkout.
- **Inventory alerts** — Notify admin via SNS when stock drops below a configurable threshold.
- **Review moderation** — Admin endpoint to flag or remove reviews.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Auth0 for authentication infrastructure
- AWS for serverless platform
- Razorpay for payment processing
- Gmail SMTP for email delivery
- Picsum Photos for placeholder images

## 📧 Support

For issues and questions:
- Create an issue in the repository
- Email: updates.mystore@gmail.com

---

**Built with ❤️ using serverless architecture**
