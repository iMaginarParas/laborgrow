# LaborGrow Backend API

LaborGrow is a production-grade service marketplace platform that connects skilled workers (laborers) with customers requiring specific tasks. This backend facilitates job creation, worker discovery, proximity-based search, and secure bookings.

## 🚀 Project Overview
The marketplace solves the problem of connecting local labor supply with immediate demand through an efficient, location-aware API. By leveraging 10 km radial searches, it ensures that jobs are visible to workers in their immediate vicinity, improving response times and reducing commute overhead.

## 🛠 Tech Stack
*   **FastAPI**: High-performance Python web framework for building APIs.
*   **Supabase (PostgreSQL)**: Scalable relational database for persistent storage and direct integration features.
*   **SQLAlchemy**: Advanced ORM for robust database interactions and migrations.
*   **Pydantic v2**: High-speed data validation and settings management.
*   **Google Maps API**: Integrated via geolocation coordinates for proximity filtering.
*   **Flutter**: (Frontend) Compatible with the LaborGrow mobile application.

## 📁 Project Structure
The backend is organized into a modular, clean structure optimized for scalability:

```text
backend/
├── main.py                 # Application entry point, middleware & API V1 routes
├── database.py             # Database engine & session management
├── config/                 # Centralized settings & environment variables
├── core/                   # Shared system features (Logging, Error handling)
├── dependencies/           # FastAPI dependency injection (Authentication)
├── models/                 # SQLAlchemy models & Pydantic schemas
├── routers/                # API versioned route handlers
├── services/               # Isolated business logic layer
├── utils/                  # Reusable helper functions (Geo-distance)
└── requirements.txt        # Project dependencies
```

## ✨ Key Features
*   **Job Lifecycle**: Create, retrieve, and manage job postings with full history.
*   **Proximity Discovery**: Efficient filtering of jobs within a **10 km radius** using the Haversine formula.
*   **Worker Marketplace**: Explore verified service providers across multiple categories (Plumbing, Painting, etc.).
*   **Secure Bookings**: End-to-end booking flow with pricing calculations and first-booking discounts.
*   **Admin Dashboard**: Dedicated APIs for marketplace management and status monitoring.
*   **Production-Ready Auth**: JWT-based authentication using `HTTPBearer` for secure endpoint access.

## ⚙️ Environment Variables
To run properly, configure the following variables in your `.env` file:

| Variable | Description |
| :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string (Supabase URI) |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Your Supabase public/service-role key |
| `SECRET_KEY` | Secure key for signing JWT tokens |
| `GOOGLE_MAPS_API_KEY` | (Optional) Required for advanced location features |

## 🛠 Installation & Local Development

### 1. Set Up Environment
Ensure you have Python 3.9+ installed.

```bash
# Clone the repository and navigate to backend
pip install -r requirements.txt
```

### 2. Configure Settings
Create a `.env` file in the root directory based on the table above.

### 3. Initialize Database
If starting fresh, run the database initialization and seed scripts:
```bash
python init_db.py
python seed_db.py
python seed_jobs.py
```

### 4. Start the Server
Run the FastAPI development server with uvicorn:
```bash
python -m uvicorn main:app --reload
```

## 📖 API Documentation
Once the server is running, access the interactive documentation at:
*   **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Redoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## ☁️ Deployment
This backend is designed to be cloud-agnostic and can be easily deployed to platforms such as **Railway**, **Render**, or **Docker** environments. Ensure all environment variables are correctly mapped in your deployment dashboard.
