"""
FastAPI Backend for Telegram Mini App.
Provides analytics and chart data endpoints.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import from services/
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from api.routes import analytics, auth, vocabulary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="English Practice Bot API",
    description="API for Telegram Mini App - Analytics and Progress",
    version="1.0.0"
)

# Configure CORS to allow requests from Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://english-bot-miniapp.vercel.app",  # Your Vercel deployment
        "https://*.vercel.app",  # Other Vercel deployments
        "http://localhost:3000",  # Local development
        "http://localhost:5173",  # Vite dev server
        "https://*.github.io",    # GitHub Pages
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(analytics.router, prefix="/api", tags=["analytics"])
app.include_router(vocabulary.router, prefix="/api", tags=["vocabulary"])


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "status": "ok",
        "message": "English Practice Bot API is running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting FastAPI server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )

