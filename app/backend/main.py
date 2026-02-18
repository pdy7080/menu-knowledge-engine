"""
Menu Knowledge Engine - FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from config import settings
from api.menu import router as menu_router
from api.admin import router as admin_router
from api.qr_menu import router as qr_router
from api.b2b import router as b2b_router
from services.cache_service import cache_service

app = FastAPI(
    title="Menu Knowledge Engine API",
    description="AI-powered Korean menu translation knowledge engine",
    version="0.1.0",
    debug=settings.DEBUG,
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    await cache_service.connect()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on application shutdown"""
    await cache_service.disconnect()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(menu_router)
app.include_router(admin_router)
app.include_router(qr_router)
app.include_router(b2b_router)

# Health check endpoint (before static files)
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Menu Knowledge Engine",
        "version": "0.1.0",
        "environment": settings.APP_ENV,
    }


# Static Files
# Admin UI
static_admin_path = Path(__file__).parent / "static" / "admin"
if static_admin_path.exists():
    app.mount("/admin", StaticFiles(directory=str(static_admin_path), html=True), name="admin")

# Frontend Landing Page (mount last to avoid conflicts with API routes)
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
