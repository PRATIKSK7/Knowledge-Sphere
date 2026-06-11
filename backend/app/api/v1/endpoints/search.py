from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_current_user
from app.models import User
from app.services.chroma_service import chroma_service
from app.agents.orchestrator import orchestrator

router = APIRouter()

@router.get("/semantic", response_model=List[Dict[str, Any]])
async def semantic_search(
    query: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=50),
    document_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    Search parsed document chunks in Vector database (Module 4 similarity/semantic search).
    """
    results = await chroma_service.search_chunks(
        query=query,
        limit=limit,
        document_id=document_id
    )
    return results

@router.post("/chat")
async def chat_with_knowledge_base(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Module 8 (RAG Engine API) + Module 15 (Research Chatbot).
    Invokes the Multi-Agent orchestrator (Module 9) to generate answers + citation markers.
    Payload keys:
    - query: str
    - history: list (for conversation memory)
    """
    query = payload.get("query", "")
    history = payload.get("history", []) # future extension for memory tracking
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"QUERY_RECEIVED: Research Chat received query: {query}")
    
    # Execute full Agent pipeline
    response_data = await orchestrator.execute_query(query, history)
    
    logger.info("ANSWER_GENERATED: Answer successfully generated")
    
    return {
        "answer": response_data["answer"],
        "analysis": response_data["analysis"],
        "confidence_score": response_data["confidence_score"],
        "citations": response_data["citations"],
        "entities": response_data["entities"],
        "relationships": response_data["relationships"],
        "graph_paths": response_data["graph_paths"]
    }
