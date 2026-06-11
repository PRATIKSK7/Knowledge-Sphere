import json
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from app.api.deps import get_current_user
from app.models import User
from app.services.neo4j_service import neo4j_service
from app.services.llm_service import LLMService
from app.services.report_generator import ReportGenerator
from app.services.chroma_service import chroma_service

router = APIRouter()

@router.get("/data")
async def get_graph_data(current_user: User = Depends(get_current_user)):
    """
    Returns full node and relationship structures for interactive Graph renders (Module 7/14).
    """
    return await neo4j_service.get_graph_data()

@router.get("/paths")
async def get_shortest_path(
    source: str = Query(...),
    target: str = Query(...),
    current_user: User = Depends(get_current_user)
):
    """
    Module 10: Multi-hop reasoning path explorer.
    """
    return await neo4j_service.find_connecting_paths(source, target)

@router.get("/gaps")
async def get_research_gaps(current_user: User = Depends(get_current_user)):
    """
    Module 11: Research gap structural hole analyzer.
    """
    return await neo4j_service.detect_research_gaps()

@router.post("/literature-review")
async def generate_lit_review(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Module 12: literature review compiler.
    """
    topic = payload.get("topic", "")
    format_style = payload.get("format", "APA")
    
    # Retrieve relevant references
    search_res = await chroma_service.search_chunks(topic, limit=8)
    context_str = ""
    for r in search_res:
        meta = r.get("metadata", {})
        context_str += f"Title: {meta.get('title', 'Paper')}\nFilename: {meta.get('filename', 'Doc')}\nText: {r['content']}\n\n"
        
    try:
        lit_review = await LLMService.generate_literature_review(
            topic=topic,
            context=context_str,
            format_style=format_style
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Literature review generation failed: No LLM provider is configured or available. "
                   f"Please set OPENAI_API_KEY, GOOGLE_API_KEY, or start an Ollama instance. Error: {e}"
        )
    return {"review": lit_review}

@router.post("/report/pdf")
async def export_pdf_report(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Module 13: Export PDF file containing graphs, entities, citations, and summaries.
    """
    # Build report payload
    query = payload.get("query", "Default Research query")
    answer = payload.get("answer", "No answer compiled yet.")
    citations = payload.get("citations", [])
    entities = payload.get("entities", [])
    confidence_score = payload.get("confidence_score", 0.85)

    data = {
        "title": f"Research Report: {query[:50]}...",
        "query": query,
        "answer": answer,
        "citations": citations,
        "entities": entities,
        "confidence_score": confidence_score
    }

    pdf_bytes = ReportGenerator.generate_pdf(data)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=report_{current_user.id}.pdf"
        }
    )
