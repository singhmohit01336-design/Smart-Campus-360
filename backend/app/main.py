
from fastapi import FastAPI

from app.api.auth import router as auth_router


app = FastAPI(
    title="SmartCampus 360 API",
    description="Cloud-Powered Campus Intelligence & Student Helpdesk Platform",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "Welcome to SmartCampus 360 API",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


app.include_router(auth_router)
