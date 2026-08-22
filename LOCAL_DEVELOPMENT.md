# NiftyFlow Local Development Guide

Welcome to the NiftyFlow local development guide. This document provides step-by-step instructions to set up the entire stack locally, including the FastAPI backend, Next.js frontend, PostgreSQL database, Redis instance, and Celery background workers.

---

## 1. Prerequisites

Ensure you have the following installed on your machine:
- **Python 3.10+**
- **Node.js 18+ & npm**
- **PostgreSQL 15+** (Running locally or via Docker)
- **Redis** (Running locally or via Docker)
- **Git**

---

## 2. Environment Variables

Create a `.env` file in the root directory. You can copy the provided `.env.example`:

```bash
cp .env.example .env
```

Ensure the following critical variables are set in your `.env`:

```ini
# Database (Update with your local Postgres credentials)
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/niftyflow

# Redis (For Celery and Rate Limiting)
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your_super_secret_jwt_key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

---

## 3. Backend Setup (FastAPI)

The backend handles API requests, database interactions, and machine learning pipelines.

### Install Dependencies
Navigate to the root directory and set up a virtual environment:

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### Database Initialization
Run Alembic migrations to build the local database schema:

```bash
alembic upgrade head
```

*(Optional)* Run the database seed scripts to populate initial mock data:
```bash
python create_initial_users.py
python seed_nse_stocks.py
```

### Start the FastAPI Server
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
The API will be available at `http://127.0.0.1:8000`. You can view the interactive Swagger documentation at `http://127.0.0.1:8000/docs`.

---

## 4. Background Workers (Celery)

NiftyFlow uses Celery for asynchronous tasks such as fetching market data from Yahoo Finance and generating XGBoost ML predictions.

In a **new terminal window** (ensure your virtual environment is activated):

```bash
# Start the Celery worker
celery -A backend.worker.celery_app worker --loglevel=info --pool=solo

# (Optional) In another terminal, start the Celery Beat scheduler for recurring tasks
celery -A backend.worker.celery_app beat --loglevel=info
```

---

## 5. Frontend Setup (Next.js)

The frontend is a React application built with Next.js and Tailwind CSS.

### Install Dependencies
```bash
cd frontend
npm install
```

### Start the Development Server
```bash
npm run dev
```
The frontend will be available at `http://localhost:3000`.

---

## 6. Testing

### Run Backend Tests (Pytest)
From the root directory, ensure your virtual environment is active:
```bash
pytest tests/ -v
```

### Run Frontend Linting
```bash
cd frontend
npm run lint
```

---

## 7. Common Troubleshooting

- **CORS Errors on Frontend:** Ensure the backend `main.py` has `http://localhost:3000` added to the `allow_origins` list in the CORS middleware.
- **"Connection Refused" (Database):** Verify that your local PostgreSQL server is running and the credentials in `.env` match your local setup.
- **ML Predictions not appearing:** Ensure the Celery worker is running. You can manually trigger predictions by running a python shell and importing `_generate_all_predictions` or waiting for the cron schedule.
- **Windows Celery Issues:** Celery on Windows requires the `--pool=solo` flag, which is included in the command above.

---
*Happy coding!*
