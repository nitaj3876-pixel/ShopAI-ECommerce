# 🛍️ ShopAI — AI-Powered E-Commerce Platform

> A modern full-stack e-commerce platform with AI-powered recommendations, intelligent shopping assistance, secure authentication, product management, cart, wishlist, orders, reviews, and a professional admin dashboard.

---

## ✨ Overview

**ShopAI** is a full-stack AI-powered e-commerce web application designed to provide a modern online shopping experience with intelligent product discovery and administration features.

The platform combines a responsive customer-facing storefront with a powerful **FastAPI backend** and a secure **Admin Dashboard** for managing products, categories, users, orders, inventory, and analytics.

The application also includes AI-powered features such as product recommendations and an AI shopping assistant to help customers discover relevant products.

---

## 🚀 Key Features

### 🛒 Customer Features

* 🔐 User Registration & Login
* 🔑 JWT Authentication
* 👤 User Profile Management
* 🔎 Product Search
* 🏷️ Category Filtering
* 💰 Price Filtering
* ⭐ Rating Filtering
* 📦 Stock Availability Filtering
* 🛍️ Shopping Cart
* ❤️ Wishlist
* 📋 Order Management
* ⭐ Product Reviews & Ratings
* 👀 Recently Viewed Products
* 🔥 Trending Products
* ⭐ Featured Products
* 🏆 Best-Seller Products
* ⚡ Flash Sale Products
* 🤖 AI Product Recommendations
* 💬 AI Shopping Assistant

---

## 👨‍💼 Admin Dashboard

ShopAI includes a dedicated administrator dashboard for managing the complete e-commerce system.

### Dashboard Analytics

* Total Users
* Total Products
* Total Orders
* Total Revenue
* Pending Orders
* Total Categories
* Total Stock
* Low Stock Products
* Out-of-Stock Products

### Product Management

Admins can:

* ➕ Add Products
* ✏️ Edit Products
* 🗑️ Archive Products
* 🔎 Search Products
* 🏷️ Filter by Category
* 📦 Monitor Stock
* 🖼️ Upload Product Images
* 💰 Manage Product Pricing
* 📝 Manage Product Descriptions

### Category Management

* Create Categories
* Manage Category Information
* Category Images
* Delete Categories

### User Management

* View Customers
* Activate/Deactivate Users
* Admin Role Protection

### Order Management

* View Orders
* Filter Orders by Status
* Update Order Status
* Track Order Information

### Analytics

* Monthly Sales
* Daily Orders
* Top-Selling Products
* Category Sales
* Revenue Analytics

---

## 🤖 AI Features

ShopAI goes beyond traditional e-commerce by integrating AI-powered functionality.

### 🧠 AI Product Recommendations

The recommendation system helps users discover similar and relevant products based on product information and user interaction.

### 💬 AI Shopping Assistant

An integrated AI chatbot assists customers with shopping-related queries and helps them discover products.

### 🎯 Personalized Discovery

The platform supports intelligent product discovery through:

* Similar Products
* Recently Viewed Products
* Trending Products
* Best Sellers
* Featured Products
* Rating-Based Discovery

---

## 🏗️ Technology Stack

### Frontend

* HTML5
* CSS3
* JavaScript
* Responsive UI
* REST API Integration

### Backend

* Python
* FastAPI
* Uvicorn
* SQLAlchemy
* Pydantic
* JWT Authentication
* Passlib
* Bcrypt

### Database

* SQLite
* SQLAlchemy ORM

### AI

* AI-powered recommendation service
* AI shopping assistant

### Tools

* Git
* GitHub
* VS Code / Codex
* Python Virtual Environment

---

## 📂 Project Structure

```text
ShopAI-ECommerce/
│
├── backend/
│   │
│   ├── app/
│   │   ├── main.py
│   │   ├── auth.py
│   │   ├── database.py
│   │   │
│   │   ├── models/
│   │   │
│   │   ├── schemas/
│   │   │
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── products.py
│   │   │   ├── cart.py
│   │   │   ├── wishlist.py
│   │   │   ├── reviews.py
│   │   │   ├── orders.py
│   │   │   ├── recommendations.py
│   │   │   ├── chatbot.py
│   │   │   └── admin.py
│   │   │
│   │   └── services/
│   │       └── recommendation.py
│   │
│   ├── uploads/
│   │   ├── products/
│   │   └── categories/
│   │
│   ├── ecommerce.db
│   ├── requirements.txt
│   ├── seed.py
│   └── .env.example
│
├── frontend/
│   ├── index.html
│   ├── admin.html
│   ├── css/
│   ├── js/
│   └── assets/
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/ShopAI-ECommerce.git
cd ShopAI-ECommerce
```

---

### 2. Create Virtual Environment

Windows:

```powershell
python -m venv .venv
```

Activate:

```powershell
.venv\Scripts\activate
```

---

### 3. Install Backend Dependencies

```powershell
cd backend
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

Create a `.env` file inside the `backend` directory.

Example:

```env
DATABASE_URL=sqlite:///./ecommerce.db

SECRET_KEY=your-secret-key

ADMIN_NAME=ShopAI Admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=your-secure-password

FRONTEND_ORIGIN=http://localhost:5500
```

### Important

Never commit your real `.env` file or secret keys to GitHub.

Use `.env.example` for public configuration templates.

---

## ▶️ Run the Backend

From the `backend` directory:

```powershell
uvicorn app.main:app --reload
```

Backend will normally be available at:

```text
http://127.0.0.1:8000
```

---

## 📚 API Documentation

FastAPI automatically provides interactive API documentation.

### Swagger UI

```text
http://127.0.0.1:8000/docs
```

### ReDoc

```text
http://127.0.0.1:8000/redoc
```

---

## 🌐 Run the Frontend

The frontend is a static HTML/CSS/JavaScript application.

Open the frontend using a local static server.

For example:

```powershell
cd frontend
python -m http.server 5500
```

Then open:

```text
http://localhost:5500
```

### Admin Dashboard

```text
http://localhost:5500/admin.html
```

---

## 🔑 Admin Authentication

The backend supports protected administrator functionality.

Admin endpoints are protected using JWT authentication and admin authorization.

Admin functionality includes:

```text
/api/admin/dashboard
/api/admin/products
/api/admin/categories
/api/admin/users
/api/admin/orders
/api/admin/reviews
/api/admin/analytics/*
```

Only authorized administrators can access protected admin operations.

---

## 📦 Product API

Customer product APIs include:

```text
GET /api/products
GET /api/products/{product_id}
GET /api/products/brands
GET /api/products/{product_id}/similar
GET /api/products/{product_id}/reviews
```

Product discovery supports:

* Search
* Category
* Brand
* Price range
* Rating
* Stock
* Featured
* Best Seller
* Trending
* Flash Sale
* Sorting

---

## 🛠️ Admin Product API

Administrators can manage products using:

```text
GET    /api/admin/products
POST   /api/admin/products
PUT    /api/admin/products/{product_id}
DELETE /api/admin/products/{product_id}
```

Product image upload:

```text
POST /api/admin/products/upload-image
```

Supported image formats:

* JPG
* PNG
* WebP
* GIF

Maximum image size:

```text
5 MB
```

Deleted products are archived rather than immediately destroying database references, helping preserve order/cart/wishlist history.

---

## 🗃️ Database

ShopAI uses:

**SQLite + SQLAlchemy ORM**

Default local database:

```text
backend/ecommerce.db
```

The application automatically initializes the required database schema when the backend starts.

Existing data should not be deleted or reset during normal development.

---

## 🔒 Security

Security features include:

* JWT-based authentication
* Password hashing
* Admin authorization
* Protected API routes
* Role-based access control
* Input validation
* Image type validation
* Image size validation
* Protected product management
* Protected order management
* Protected user management

---

## 📸 Screenshots

Add your project screenshots here after uploading them to the repository.

Example:

```markdown
![Home Page](screenshots/home.png)

![Products](screenshots/products.png)

![Admin Dashboard](screenshots/admin-dashboard.png)

![Add Product](screenshots/add-product.png)
```

Recommended screenshots:

1. Home Page
2. Product Listing
3. Product Details
4. Shopping Cart
5. Wishlist
6. Login/Register
7. Admin Dashboard
8. Product Management
9. Add Product
10. Orders
11. AI Shopping Assistant

---

## 📊 System Architecture

```text
                  ┌─────────────────────┐
                  │      Customer       │
                  │   Web Frontend      │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │     FastAPI API     │
                  │     Backend         │
                  └──────────┬──────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
   Authentication       E-Commerce          AI Services
      JWT                 APIs             Recommendations
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │   SQLAlchemy ORM    │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │   SQLite Database   │
                  └─────────────────────┘

                    ┌─────────────────┐
                    │  Admin Panel    │
                    │  Dashboard      │
                    └────────┬────────┘
                             │
                             ▼
                    Protected Admin APIs
```

---

## 🧪 Health Check

The backend provides a health endpoint:

```text
GET /api/health
```

Expected response:

```json
{
  "status": "ok"
}
```

---

## 🎯 Project Objectives

The main objectives of ShopAI are:

* Build a complete full-stack e-commerce application
* Provide secure authentication
* Implement scalable REST APIs
* Integrate AI into online shopping
* Provide personalized product discovery
* Build an administrative management system
* Implement inventory management
* Provide order and customer management
* Create a responsive and user-friendly shopping experience

---

## 🚀 Future Enhancements

Potential future improvements include:

* 💳 Real Payment Gateway Integration
* ☁️ Cloud Image Storage
* 📧 Email Notifications
* 📱 Progressive Web App
* 📈 Advanced Business Intelligence Dashboard
* 🔔 Real-Time Notifications
* 🧠 More Personalized AI Recommendations
* 🗣️ Voice-Based Shopping Assistant
* 📦 Advanced Delivery Tracking
* 🌐 Production Cloud Deployment

---

## 👩‍💻 Author

**Nita Jadhav**

Diploma in Information Technology

---

## ⭐ Support

If you find this project useful, consider giving the repository a ⭐ on GitHub.

---

## 📄 License

This project is developed for educational, internship, and portfolio purposes.

You may modify and extend the project for learning and demonstration.
