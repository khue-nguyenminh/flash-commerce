# Flash Commerce API

A RESTful e-commerce backend built with FastAPI, SQLAlchemy, and Microsoft SQL Server.

The project demonstrates authentication, role-based authorization, product and order management, transactional inventory control, coupon usage, payment processing, reviews, and concurrency-safe order creation.

## Key Features

### Authentication and authorization

- Customer registration and login
- JWT bearer authentication
- Customer and Admin roles
- Ownership checks for protected resources
- Admin-only management endpoints

### Product catalog

- Product CRUD
- Hierarchical categories
- Product-category relationships
- Search, price filtering, and pagination
- Stock quantity management

### Orders and concurrency

- Create orders containing multiple products
- Server-side price calculation
- Transactional stock deduction
- SQL Server row-level locking
- Deterministic product locking order
- Prevention of overselling during concurrent requests
- Customer order history and detail
- Safe cancellation with stock restoration
- Protection against duplicate cancellation

### Coupons

- Percentage-based discounts
- Validity period validation
- Global usage limits
- Concurrency-safe coupon usage
- Coupon usage restoration when an order is cancelled

### Payments

- Simulated Card, Bank Transfer, and E-Wallet payments
- Payment amount derived from the order
- Protection against duplicate payment
- Payment and Order status updated in one transaction
- Ownership validation

### Order workflow

```text
Pending → Paid → Processing → Shipped → Completed
    │
    └──→ Cancelled
```

- Payment changes an Order from `Pending` to `Paid`
- Admin advances paid Orders through fulfilment
- Customers can only cancel `Pending` Orders
- Invalid status transitions are rejected

### Reviews

- Ratings from 1 to 5
- Only customers with a completed purchase can review a product
- One review per customer per product
- Customers can update or delete their own reviews
- Product reviews can be viewed publicly

## Technology Stack

- Python 3.12
- FastAPI
- SQLAlchemy 2
- Pydantic 2
- Microsoft SQL Server 2022
- JWT authentication
- Docker Compose
- Uvicorn

## Project Structure

```text
flash-commerce/
├── app/
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   └── security.py
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   └── main.py
├── scripts/
│   ├── init_database.sql
│   └── test_concurrency.py
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/khue-nguyenminh/flash-commerce.git
cd flash-commerce
```

### 2. Create a virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

On Windows:

```powershell
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Update `.env` with a strong SQL Server password and JWT secret:

```env
MSSQL_SA_PASSWORD=your-strong-local-password
DATABASE_HOST=127.0.0.1
DATABASE_PORT=1433
DATABASE_NAME=FlashCommercePro
DATABASE_USER=sa
JWT_SECRET_KEY=your-secure-random-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Do not commit `.env`.

### 5. Start SQL Server

```bash
docker compose up -d
```

Check that the container is running:

```bash
docker compose ps
```

The SQL Server image runs through AMD64 emulation on Apple Silicon because the Compose configuration specifies:

```yaml
platform: linux/amd64
```

### 6. Initialize the database

Run the initialization script inside the SQL Server container:

```bash
docker exec -i flash-commerce-sqlserver \
  /opt/mssql-tools18/bin/sqlcmd \
  -S localhost \
  -U sa \
  -P "YOUR_MSSQL_PASSWORD" \
  -C \
  < scripts/init_database.sql
```

Replace `YOUR_MSSQL_PASSWORD` with the password configured in `.env`.

### 7. Start the API

```bash
uvicorn app.main:app --reload
```

The application will be available at:

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI schema: http://127.0.0.1:8000/openapi.json
- Health check: http://127.0.0.1:8000/health

## API Overview

| Area | Main endpoints |
|---|---|
| Authentication | `/auth/register`, `/auth/login`, `/auth/me` |
| Addresses | `/addresses` |
| Categories | `/categories` |
| Products | `/products` |
| Orders | `/orders`, `/orders/{order_id}/cancel` |
| Admin Orders | `/admin/orders`, `/admin/orders/{order_id}/status` |
| Coupons | `/coupons` |
| Payments | `/payments`, `/payments/order/{order_id}` |
| Reviews | `/reviews`, `/reviews/product/{product_id}`, `/reviews/me` |

Full request and response schemas are available in Swagger UI.

## Authentication

Register or log in through the authentication endpoints. The login endpoint returns a JWT access token.

In Swagger UI:

1. Call `POST /auth/login`.
2. Copy the returned access token.
3. Select **Authorize**.
4. Enter the bearer token.
5. Call the protected endpoints.

Admin endpoints require a User account with the Admin role.

## Concurrency Protection

Order creation uses a database transaction and SQL Server update locks:

```sql
WITH (UPDLOCK, ROWLOCK)
```

Products are locked in deterministic UUID order before stock is checked and deducted. This prevents concurrent requests from purchasing more units than are available and reduces deadlock risk for multi-product orders.

Coupon rows are also locked before checking and updating their usage count. Payment and cancellation operations lock their Order rows to prevent duplicate processing.

If any operation fails, the entire transaction is rolled back.

## Running the Concurrency Test

Before running the test:

1. Start the API.
2. Create or select a Customer account.
3. Create an Address for that Customer.
4. Create a Product with `stock_quantity` equal to `1`.
5. Copy the Address ID and Product ID.

Run:

```bash
python scripts/test_concurrency.py
```

The script sends ten order requests at approximately the same time.

Expected result:

```text
Response counts:
{201: 1, 409: 9}

Final stock:
0

PASSED: no overselling occurred.
```

Exactly one request should create an Order. The other requests should receive `409 Conflict`, and the final stock must remain `0`.

## Business Rules

- Prices and payment amounts are calculated by the server.
- An Address must belong to the authenticated Customer.
- An Order cannot contain the same Product more than once.
- Stock cannot fall below zero.
- Coupons must be active and below their usage limit.
- Only `Pending` Orders can be cancelled.
- Paid Orders cannot be paid again.
- Admin Order status transitions must occur in the correct sequence.
- Only completed purchases are eligible for product reviews.
- A Customer can review each Product only once.

## Current Scope

Payment processing is simulated locally. The project does not connect to an external payment provider such as Stripe, VNPay, or MoMo.

The API focuses on backend business logic, transaction safety, authorization, and concurrency handling.