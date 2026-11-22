from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.tickets import router as tickets_router
from app.api.comments import router as comments_router
from app.api.attachments import router as attachments_router
from app.api.intelligence import router as intelligence_router
from app.api.sla import router as sla_router
from app.api.qr import router as qr_router
from app.api.knowledge_base import router as knowledge_base_router
from app.api.analytics import router as analytics_router
from app.api.departments import router as departments_router
from app.core.config import settings


app = FastAPI(
    title="SmartCampus 360 API",
    description="Cloud-Powered Campus Intelligence & Student Helpdesk Platform",
    version="1.0.0",
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


# Register API Routers
app.include_router(auth_router)
app.include_router(tickets_router)
app.include_router(comments_router)
app.include_router(attachments_router)
app.include_router(intelligence_router)
app.include_router(sla_router)
app.include_router(qr_router)
app.include_router(knowledge_base_router)
app.include_router(analytics_router)
app.include_router(departments_router)
