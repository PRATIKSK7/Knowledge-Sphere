import logging
import asyncio
from fastapi import APIRouter, HTTPException
from app.services.chroma_service import chroma_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/chroma")
async def chroma_health():
    """
    Liveness probe for the ChromaDB vector store.

    Returns:
        200 {"status": "healthy"}  — server is reachable and heartbeat is valid.
        503 {"detail": "..."}      — server is unreachable or returned an error.
    """
    # health_check() is synchronous (blocking HTTP); run in thread pool to avoid
    # blocking the uvicorn event loop.
    result = await asyncio.to_thread(chroma_service.health_check)
    if result["status"] != "healthy":
        logger.error(f"[Health] ChromaDB unhealthy: {result.get('error')}")
        raise HTTPException(
            status_code=503,
            detail=f"ChromaDB unhealthy: {result.get('error', 'unknown error')}"
        )
    logger.info("[Health] ChromaDB health check passed")
    return {"status": "healthy"}

@router.get("/ai")
async def ai_health():
    """
    Diagnostic endpoint to determine which LLM is active and what features it supports.
    """
    from app.core.config import settings
    
    # Evaluate configured provider keys
    openai_ok = bool(settings.OPENAI_API_KEY)
    google_ok = bool(settings.GOOGLE_API_KEY)
    
    provider = settings.DEFAULT_LLM_PROVIDER
    is_ready = False
    if provider == "openai" and openai_ok:
        is_ready = True
    elif provider == "gemini" and google_ok:
        is_ready = True
    elif provider == "ollama":
        # Ollama local instance assumed ready or will timeout
        is_ready = True
    elif openai_ok or google_ok:
        # Fallback is ready
        is_ready = True
        provider = "openai" if openai_ok else "gemini"
        
    return {
        "provider": provider,
        "is_ready": is_ready,
        "chat": is_ready,
        "embeddings": True, # Embeddings use local ONNX Model (all-MiniLM)
        "knowledge_graph": is_ready
    }
