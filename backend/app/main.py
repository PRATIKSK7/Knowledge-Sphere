import time
import logging
from fastapi import FastAPI, Request, status, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup: Create Postgres tables on startup if they don't exist
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully.")

    # Validate AI Configuration
    logger.info("Validating AI Configuration...")
    llm_provider = settings.DEFAULT_LLM_PROVIDER
    if llm_provider == "openai" and not settings.is_real_key(settings.OPENAI_API_KEY):
        msg = "Startup Validation Failed: DEFAULT_LLM_PROVIDER is 'openai' but no valid OPENAI_API_KEY is configured."
        logger.error(msg)
        raise ValueError(msg)
    elif llm_provider == "gemini" and not settings.is_real_key(settings.GOOGLE_API_KEY):
        msg = "Startup Validation Failed: DEFAULT_LLM_PROVIDER is 'gemini' but no valid GOOGLE_API_KEY is configured."
        logger.error(msg)
        raise ValueError(msg)

    emb_provider = settings.DEFAULT_EMBEDDING_PROVIDER
    if emb_provider == "openai" and not settings.is_real_key(settings.OPENAI_API_KEY):
        msg = "Startup Validation Failed: DEFAULT_EMBEDDING_PROVIDER is 'openai' but no valid OPENAI_API_KEY is configured."
        logger.error(msg)
        raise ValueError(msg)
    elif emb_provider == "gemini" and not settings.is_real_key(settings.GOOGLE_API_KEY):
        msg = "Startup Validation Failed: DEFAULT_EMBEDDING_PROVIDER is 'gemini' but no valid GOOGLE_API_KEY is configured."
        logger.error(msg)
        raise ValueError(msg)

    logger.info(f"AI Provider ready. Preferred LLM: '{llm_provider}', Preferred Embedding: '{emb_provider}'")

    # Warm up ChromaDB connection and embedding model so first search is fast
    try:
        from app.services.chroma_service import chroma_service
        logger.info("Warming up ChromaDB connection...")
        chroma_service.health_check()  # triggers lazy client init + heartbeat
        logger.info("ChromaDB connection warm.")

        logger.info("Warming up embedding service (API based)...")
        # No local ONNX model to load anymore
        logger.info("Embedding service warm.")
    except Exception as e:
        logger.warning(f"ChromaDB warmup failed (non-fatal, will retry on first request): {e}")
    
    yield
    
    # Cleanup: Close connections if any
    logger.info("Shutting down application server...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Industry-Grade AI Knowledge Graph Research Intelligence Platform backend",
    lifespan=lifespan
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin).strip("/") for origin in settings.ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting simple in-memory middleware fallback
rate_limit_store = {}

@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    # Simple IP-based rate limiting (Module 18 & 19)
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()
    
    # Clean old records
    rate_limit_store[client_ip] = [t for t in rate_limit_store.get(client_ip, []) if current_time - t < 60]
    
    if len(rate_limit_store[client_ip]) >= settings.RATE_LIMIT_PER_MINUTE:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests. Please slow down."}
        )
        
    rate_limit_store[client_ip].append(current_time)
    
    # Timing header
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response

# Security headers (XSS/CSRF context, clickjacking, etc.)
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
    return response

# Mount APIs
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }
