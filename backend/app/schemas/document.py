from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel
from app.models import IngestionStatus

class DocumentBase(BaseModel):
    title: str
    filename: str
    filepath: str
    file_size: int
    mime_type: str

class DocumentCreate(DocumentBase):
    uploaded_by: int

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[IngestionStatus] = None
    error_message: Optional[str] = None
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    publication_date: Optional[datetime] = None
    references: Optional[List[str]] = None

class DocumentResponse(BaseModel):
    id: int
    title: str
    filename: str
    file_size: int
    mime_type: str
    status: IngestionStatus
    error_message: Optional[str] = None
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    publication_date: Optional[datetime] = None
    references: Optional[Any] = None
    uploaded_by: int
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str
    chroma_id: str

    class Config:
        from_attributes = True
