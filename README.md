# LINE LON Integration Service for Thai Watsadu

A backend service built with Python and FastAPI to integrate Thai Watsadu's internal systems with EGG Digital's LINE Official Notification (LON) API. It supports environment isolation (TEST / PROD), automated delivery status tracking via webhooks, and an automatic SMS fallback mechanism when LINE message delivery fails.

Additionally, it provides an internal monitoring dashboard built with Streamlit.

---

## Features

- **Robust REST API**: Strong data validation using Pydantic, ensuring requests strictly match EGG Digital's required fields for all template types (`DELIVERY`, `PAYMENT_COMPLETE`, etc.).
- **Automatic Environment Selection**: Maps requests to the correct API keys and template IDs for `TEST` and `PROD`.
- **Delivery Report (DLR) Webhook**: Receives status updates from EGG Digital and logs them in a SQLite/PostgreSQL database.
- **SMS Fallback**: Automatically triggers an asynchronous SMS send if the LINE message is undelivered, expired, or rejected.
- **LINE Webhook Forwarding**: Forwards incoming LINE OA events to EGG Digital's webhook url for user tracking.
- **Streamlit Dashboard**: A dashboard to review logs, analyze delivery success metrics, and export data to CSV.

---

## Installation & Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and fill in the required API keys and template UUIDs:
   ```bash
   copy .env.example .env
   ```

3. **Run the FastAPI Server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   Access the interactive API documentation at: [http://localhost:8000/docs](http://localhost:8000/docs)

4. **Run the Streamlit Dashboard**:
   ```bash
   streamlit run dashboard/app.py
   ```
   Access the dashboard at: [http://localhost:8501](http://localhost:8501)
