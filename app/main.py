from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.database import engine, Base
from app.routers import send, webhook
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Create Database tables on startup
logger.info("Initializing database and tables...")
Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI(
    title="LINE Official Notification (LON) Integration Service",
    description="Backend API wrapper for Thai Watsadu to route LINE notifications to EGG Digital LON API, including SMS fallback.",
    version="1.0.0",
)

# Bind Routers
app.include_router(send.router)
app.include_router(webhook.router)

@app.get("/", include_in_schema=False)
async def root():
    """Redirect root access to OpenAPI documentation"""
    return RedirectResponse(url="/docs")
