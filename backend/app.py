"""
AI Study & Career Copilot — Backend Server Entrypoint
FastAPI application controlling APIs, business logic, AI orchestration, database persistence, and static UI serving.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import sys

# Ensure root project directory is on the Python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.routes.learning import router as learning_router
from database.db import init_db

# Initialize database schema on startup
init_db()

app = FastAPI(
    title="AI Study & Career Copilot API",
    description="Backend API powering the closed-loop learning cycle: Learn -> Practice -> Test -> Analyze -> Improve -> Test Again",
    version="1.0.0"
)

# Enable CORS for local development and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register REST API Router
app.include_router(learning_router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catches uncaught exceptions to ensure the user receives a clean,
    user-friendly error response instead of raw stack traces.
    """
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "An unexpected error occurred while processing your request.",
            "detail": str(exc) if os.getenv("DEBUG") == "true" else "Internal server error"
        }
    )

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint to verify backend status.
    """
    return {
        "status": "healthy",
        "app": "AI Study & Career Copilot",
        "version": "1.0.0",
        "learning_cycle": ["Learn", "Practice", "Test", "Analyze", "Improve", "Test Again"]
    }

# Mount static frontend files
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

if os.path.exists(FRONTEND_DIR):
    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

if __name__ == "__main__":
    print("Starting AI Study & Career Copilot on http://127.0.0.1:8000 ...")
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
