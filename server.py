"""
server.py
Main FastAPI application and Uvicorn server runner for Blink.
Serves both the REST/WebSocket API and the built React + Vite frontend.
"""

import os
import sys
import webbrowser
import threading
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.routes import router as api_router, ws_router
from core.database import init_db
from core.logger_setup import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("FastAPI Backend initialized.")
    yield


app = FastAPI(
    title="Blink — Eye Health Monitor",
    description="Full-stack Eye Fatigue & Blink Tracking Platform",
    version="2.0.0",
    lifespan=lifespan,
)

# Enable CORS for Vite dev server and local clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API and WebSocket routes
app.include_router(api_router)
app.include_router(ws_router)

# Mount frontend static assets if dist directory exists
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")
ASSETS_DIR = os.path.join(FRONTEND_DIST, "assets")

if os.path.exists(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

if os.path.exists(FRONTEND_DIST):
    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa_fallback(full_path: str):
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
else:
    @app.get("/")
    def index():
        return {
            "message": "Blink API is running! Frontend is in development mode or not yet built.",
            "docs": "/docs",
            "video_feed": "/api/video_feed",
        }


def open_browser():
    """Opens browser after server starts."""
    import time
    time.sleep(1.2)
    webbrowser.open("http://localhost:8000")


def main():
    logger.info("Starting Blink Server on http://127.0.0.1:8000")
    if "--no-browser" not in sys.argv:
        threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
