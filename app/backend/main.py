"""
Menu Knowledge Engine - FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from api.menu import router as menu_router

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
