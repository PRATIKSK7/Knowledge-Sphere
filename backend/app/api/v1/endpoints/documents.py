import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.models import Document, IngestionStatus, User
from app.schemas.document import DocumentResponse
from app.api.deps import get_current_user
from app.workers.tasks import process_document_task
from app.services.chroma_service import chroma_service

router = APIRouter()

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"UPLOAD START: received file '{file.filename}', content_type='{file.content_type}'")
        
        # Check extensions
        ext = os.path.splitext(file.filename)[1].lower().replace(".", "")
        allowed = settings.ALLOWED_EXTENSIONS.split(",")
        if ext not in allowed:
            logger.error(f"UPLOAD FAILED: Unsupported extension '{ext}'")
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: .{ext}"
            )

        # Validate common MIME types
        mime = file.content_type or ""
        if ext == "pdf" and not mime.startswith("application/pdf") and not mime.startswith("application/x-pdf") and not mime.startswith("application/octet-stream"):
            logger.error(f"UPLOAD FAILED: PDF MIME type not recognized: {mime}")
            raise HTTPException(
                status_code=400,
                detail="PDF MIME type not recognized."
            )

        # Make upload directory if not exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Save file to disk
        file_path = os.path.join(settings.UPLOAD_DIR, f"{current_user.id}_{file.filename}")
        
        # Read file content and write
        content = await file.read()
        file_size = len(content)
        logger.info(f"UPLOAD DEBUG: Read {file_size} bytes for file '{file.filename}'")
        
        if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            logger.error(f"UPLOAD FAILED: File size {file_size} exceeds {settings.MAX_FILE_SIZE_MB}MB limit")
            raise HTTPException(
                status_code=400,
                detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB"
            )

        with open(file_path, "wb") as f:
            f.write(content)

        # Check for duplicates (filename & user size match)
        logger.info(f"UPLOAD DEBUG: Checking for duplicate document '{file.filename}' (size={file_size})")
        result = await db.execute(
            select(Document).where(
                Document.filename == file.filename,
                Document.uploaded_by == current_user.id,
                Document.file_size == file_size
            )
        )
        duplicate = result.scalars().first()
        if duplicate:
            logger.info(f"UPLOAD DEBUG: Duplicate found (id={duplicate.id}, status={duplicate.status})")
            if duplicate.status == IngestionStatus.FAILED:
                logger.info(f"UPLOAD START: Retrying failed document {duplicate.id}")
                duplicate.status = IngestionStatus.PENDING
                await db.commit()
                logger.info(f"TASK QUEUED: Re-queueing document {duplicate.id}")
                process_document_task.delay(duplicate.id)
                return duplicate
            # File path remains active, reuse existing doc representation
            logger.info(f"UPLOAD FINISHED: Returned existing duplicate doc {duplicate.id}")
            return duplicate

        logger.info("UPLOAD_STARTED: New document received, saving to DB")
        doc = Document(
            title=os.path.splitext(file.filename)[0].replace("_", " ").title(),
            filename=file.filename,
            filepath=file_path,
            file_size=file_size,
            mime_type=file.content_type or f"application/{ext}",
            status=IngestionStatus.PENDING,
            uploaded_by=current_user.id
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        
        logger.info(f"UPLOAD SAVED: Document committed to DB with id {doc.id}")

        # Trigger background parsing Celery task
        logger.info(f"TASK QUEUED: Queueing celery task for document_id {doc.id}")
        process_document_task.delay(doc.id)

        return doc
        
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.exception(f"UPLOAD EXCEPTION: Unhandled error during upload: {e}")
        raise

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document).where(Document.uploaded_by == current_user.id))
    return result.scalars().all()

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.uploaded_by == current_user.id
        )
    )
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.uploaded_by == current_user.id
        )
    )
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Clean local disk file
    if os.path.exists(doc.filepath):
        try:
            os.remove(doc.filepath)
        except Exception:
            pass

    # Clean Vector chunks
    await chroma_service.delete_document_chunks(doc.id)

    # Delete from postgres
    await db.delete(doc)
    await db.commit()
    return
