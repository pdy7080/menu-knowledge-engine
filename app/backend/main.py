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

app = FastAPI(
    title="Menu Knowledge Engine API",
    description="AI-powered Korean menu translation knowledge engine",
    version="0.1.0",
    debug=settings.DEBUG,
)

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

# Static Files (Admin UI)
static_path = Path(__file__).parent / "static" / "admin"
if static_path.exists():
    app.mount("/admin", StaticFiles(directory=str(static_path), html=True), name="admin")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Menu Knowledge Engine",
        "version": "0.1.0",
        "environment": settings.APP_ENV,
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Menu Knowledge Engine API",
        "docs": "/docs",
        "health": "/health",
        "api": {
            "concepts": "/api/v1/concepts",
            "modifiers": "/api/v1/modifiers",
            "canonical-menus": "/api/v1/canonical-menus",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
