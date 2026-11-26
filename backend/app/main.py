from fastapi import FastAPI

from app.core.config import settings
from app.api.routes.health import router as health_router
from app.api.routes.payments import router as payments_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Simulated UPI Payment Gateway and Fraud Detection System",
    version="1.0.0"
)

app.include_router(health_router)
app.include_router(payments_router)

@app.get("/")
def root():
    return {
        "message": "UPI Payment and Fraud Detection API",
        "status": "running"
    }