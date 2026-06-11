from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models import User, Document
from app.services.neo4j_service import neo4j_service

router = APIRouter()

@router.get("/")
async def get_analytics_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 16: Analytics Dashboard counters.
    """
    # 1. Total parsed docs
    docs_result = await db.execute(
        select(func.count(Document.id)).where(Document.uploaded_by == current_user.id)
    )
    total_documents = docs_result.scalar() or 0

    # 2. Neo4j analytics
    graph_stats = await neo4j_service.get_analytics()

    # 3. Trending topics mock list
    trending_topics = [
        {"topic": "Graph Neural Networks", "count": 24, "growth": "+12%"},
        {"topic": "Causal Reasoning", "count": 18, "growth": "+8%"},
        {"topic": "Multi-hop RAG Pipelines", "count": 15, "growth": "+15%"},
        {"topic": "Explainable AI in Clinical Trials", "count": 9, "growth": "+4%"}
    ]

    return {
        "total_documents": total_documents,
        "graph": graph_stats,
        "trending_topics": trending_topics,
        "user_activity": [
            {"date": "2026-06-01", "uploads": 2, "queries": 12},
            {"date": "2026-06-02", "uploads": 4, "queries": 15},
            {"date": "2026-06-03", "uploads": 1, "queries": 8},
            {"date": "2026-06-04", "uploads": 5, "queries": 22},
            {"date": "2026-06-05", "uploads": 3, "queries": 19},
            {"date": "2026-06-06", "uploads": total_documents, "queries": 25}
        ]
    }
