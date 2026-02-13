from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api import vehicles, invoices, recommendations, timeline
from app.utils.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MaintenanceGuard API",
    description="Vehicle maintenance tracking and upsell detection system",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(vehicles.router, prefix="/api/vehicles", tags=["vehicles"])
app.include_router(invoices.router, prefix="/api/invoices", tags=["invoices"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(timeline.router, prefix="/api/timeline", tags=["timeline"])

@app.get("/")
async def root():
    return {
        "message": "MaintenanceGuard API",
        "version": "0.1.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
