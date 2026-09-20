"""
LegalAssist AI - Main FastAPI Application
AI-powered legal document analysis and assistance
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pathlib import Path
import time

from .config import APP_NAME, APP_VERSION, DEBUG, GEMINI_API_KEY, AUTO_DELETE_MINUTES
from .routes import documents, chat, compare
from .utils.document_store import document_store

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("legalassist")

# Background task for auto-deleting expired documents
async def cleanup_expired_docs():
    """Periodically clean up documents older than 10 minutes."""
    while True:
        try:
            deleted = document_store.cleanup_expired_documents()
            if deleted > 0:
                logger.info("Auto-cleanup: removed %d expired documents", deleted)
        except Exception as e:
            logger.error("Cleanup error: %s", e)
        await asyncio.sleep(60)  # Check every minute

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting LegalAssist AI...")
    task = asyncio.create_task(cleanup_expired_docs())
    yield
    # Shutdown
    task.cancel()
    logger.info("Shutting down LegalAssist AI...")

# Create FastAPI app
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="AI-powered legal document analysis and assistance platform",
    debug=DEBUG,
    lifespan=lifespan
)

# CORS middleware - locked down to same-origin only
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)

# Rate limiting middleware
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 30, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old entries
        self.requests = {k: v for k, v in self.requests.items() if now - v[-1] < self.window_seconds}

        # Count recent requests
        recent = [t for t in self.requests.get(client_ip, []) if now - t < self.window_seconds]
        if len(recent) >= self.max_requests:
            return Response(
                content='{"detail":"Rate limit exceeded. Try again later."}',
                status_code=429,
                media_type="application/json"
            )

        self.requests.setdefault(client_ip, []).append(now)
        return await call_next(request)

app.add_middleware(RateLimitMiddleware, max_requests=30, window_seconds=60)

# No-cache middleware for static files
class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.endswith(('.html', '.js', '.css')):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response

app.add_middleware(NoCacheMiddleware)

# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:;"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Include routers
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(compare.router)

# Frontend directory
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# Mount static files
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css", html=False), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js", html=False), name="js")


# Serve frontend pages
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the main dashboard page."""
    return FileResponse(FRONTEND_DIR / "index.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"})


@app.get("/analyze", response_class=HTMLResponse)
async def serve_analyze():
    """Serve the document analysis page."""
    return FileResponse(FRONTEND_DIR / "analyze.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"})


@app.get("/compare", response_class=HTMLResponse)
async def serve_compare():
    """Serve the document comparison page."""
    return FileResponse(FRONTEND_DIR / "compare.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"})


@app.get("/chat", response_class=HTMLResponse)
async def serve_chat():
    """Serve the document Q&A page."""
    return FileResponse(FRONTEND_DIR / "chat.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"})


@app.get("/legal-info", response_class=HTMLResponse)
async def serve_legal_info():
    """Serve the legal information page."""
    return FileResponse(FRONTEND_DIR / "legal-info.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"})


@app.get("/about", response_class=HTMLResponse)
async def serve_about():
    """Serve the about page."""
    return FileResponse(FRONTEND_DIR / "about.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"})


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": APP_NAME,
        "version": APP_VERSION,
        "gemini_configured": bool(GEMINI_API_KEY)
    }


# API status endpoint
@app.get("/api/status")
async def api_status():
    """API status with configuration info."""
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "gemini_configured": bool(GEMINI_API_KEY),
        "gemini_model": "gemini-1.5-flash" if GEMINI_API_KEY else None,
        "auto_delete_minutes": AUTO_DELETE_MINUTES
    }
