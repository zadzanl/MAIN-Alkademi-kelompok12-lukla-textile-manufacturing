"""
Main FastAPI Application
Sampling & Spec R&D Module
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import create_api_router

# Load environment variables from .env file
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Sampling & Spec R&D API",
    description="Time Study Recording and Specification Version Tracking",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3009", "http://127.0.0.1:3009", "http://localhost:3007", "http://127.0.0.1:3007"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
router = create_api_router()
app.include_router(router)

# Health check endpoint (at root level for backward compatibility)
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "sampling-spec-rnd-api"}

# Health check endpoint (also at API level for frontend)
@app.get("/api/sampling-spec-rnd/health")
def health_check_api():
    """Health check endpoint"""
    return {"status": "healthy", "service": "sampling-spec-rnd-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007, reload=True)
