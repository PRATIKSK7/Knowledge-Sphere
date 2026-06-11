import asyncio
import logging
from celery import shared_task
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.models import Document, DocumentChunk, IngestionStatus, User
from app.services.document_parser import DocumentParser
from app.services.chroma_service import chroma_service
from app.services.neo4j_service import neo4j_service
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

# Re-initialize engine for Celery sub-processes (must be safe across forks/threads)
engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

def run_async(coro):
    """
    Helper to run asynchronous coroutines from Celery worker threads.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@shared_task(name="app.workers.tasks.process_document_task", queue="documents", bind=True, max_retries=3)
def process_document_task(self, document_id: int):
    logger.info(f"TASK_RECEIVED: Celery worker received document_id {document_id}")
    try:
        return run_async(async_process_document(document_id))
    except Exception as exc:
        logger.error(f"process_document_task failed, retrying... {exc}")
        raise self.retry(exc=exc, countdown=10 * (self.request.retries + 1))

async def async_process_document(document_id: int):
    async with async_session_maker() as db:
        # 1. Fetch document
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalars().first()
        if not doc:
            logger.error(f"Document with id {document_id} not found in database.")
            return

        try:
            # 2. Set parsing status
            logger.info(f"STATUS UPDATE: Setting PARSING status for doc_id {document_id}")
            doc.status = IngestionStatus.PARSING
            
            # Clean up any existing chunks from previous failed runs
            await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
            await db.commit()

            # 3. Extract text
            logger.info(f"PARSING_STARTED: Extracting text from {doc.filepath}")
            raw_text = DocumentParser.extract_text(doc.filepath, doc.mime_type)
            clean_text = DocumentParser.clean_text(raw_text)

            # 4. Extract metadata & update
            logger.info(f"PARSING_STARTED: Extracting metadata for doc_id {document_id}")
            metadata = DocumentParser.extract_metadata(clean_text, doc.filename)
            doc.abstract = metadata["abstract"]
            doc.keywords = metadata["keywords"]
            doc.authors = metadata["authors"]
            doc.references = metadata["references"]
            
            # 5. Chunking (Module 3)
            logger.info(f"STATUS UPDATE: Setting CHUNKING status for doc_id {document_id}")
            doc.status = IngestionStatus.CHUNKING
            await db.commit()

            logger.info(f"CHUNKING_STARTED: Chunking document {document_id}")
            chunks = DocumentParser.chunk_text(clean_text)
            logger.info(f"CHUNKING_STARTED: Generated {len(chunks)} chunks for doc_id {document_id}")
            
            # 6. Embed and Index in ChromaDB (Module 4)
            logger.info(f"STATUS UPDATE: Setting INDEXING status for doc_id {document_id}")
            doc.status = IngestionStatus.INDEXING
            await db.commit()

            chroma_chunks = []
            db_chunks = []
            
            for idx, chunk_content in enumerate(chunks):
                chroma_id = f"doc_{doc.id}_chunk_{idx}"
                db_chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=idx,
                    content=chunk_content,
                    token_count=len(chunk_content.split()), # crude approximation
                    chroma_id=chroma_id
                )
                db_chunks.append(db_chunk)
                
                chroma_chunks.append({
                    "id": chroma_id,
                    "content": chunk_content,
                    "metadata": {
                        "filename": doc.filename,
                        "title": doc.title
                    }
                })

            # Save chunks to PostgreSQL
            db.add_all(db_chunks)
            await db.commit()

            # Save chunks to Vector database
            logger.info(f"EMBEDDING_STARTED: Generating embeddings for doc_id {document_id}")
            logger.info(f"CHROMA_INSERTED: Storing chunks in ChromaDB for doc_id {document_id}")
            await chroma_service.add_chunks(doc.id, chroma_chunks)

            # 7. Knowledge extraction (Module 5 & 6) and Graph Builder (Module 7)
            logger.info(f"STATUS UPDATE: Setting EXTRACTING status for doc_id {document_id}")
            logger.info(f"GRAPH_CREATED: Knowledge extraction (Neo4j) for doc_id {document_id}")
            doc.status = IngestionStatus.EXTRACTING
            await db.commit()

            # We process ALL chunks in batches to build the knowledge graph thoroughly.
            # Limit batch size to 5 to avoid overloading the LLM concurrently.
            batch_size = 5
            for i in range(0, len(db_chunks), batch_size):
                batch = db_chunks[i:i + batch_size]
                logger.info(f"GRAPH_EXTRACTION: Processing batch {i//batch_size + 1}/{(len(db_chunks) + batch_size - 1)//batch_size} (chunks {i} to {i+len(batch)-1})")
                
                # We process sequentially in the batch to avoid massive parallel rate limits on external LLMs, 
                # but we catch exceptions per-chunk so one failure doesn't halt the document graph build.
                for chunk in batch:
                    try:
                        extracted = await LLMService.extract_knowledge(chunk.content)
                        entities = extracted.get("entities", [])
                        relations = extracted.get("relationships", [])

                        # Add Paper node
                        await neo4j_service.create_node(
                            label="Paper",
                            name=doc.title,
                            properties={
                                "document_id": doc.id,
                                "filename": doc.filename,
                                "abstract": doc.abstract or ""
                            }
                        )

                        # Add Author nodes and REFERENCES relationships
                        if doc.authors:
                            for author in doc.authors:
                                await neo4j_service.create_node(label="Author", name=author)
                                await neo4j_service.create_relationship(
                                    source_label="Author", source_name=author,
                                    target_label="Paper", target_name=doc.title,
                                    rel_type="PUBLISHED"
                                )

                        # Store entities and relations extracted
                        for entity in entities:
                            ent_label = entity.get("label", "Concept")
                            ent_name = entity.get("name")
                            if ent_name:
                                await neo4j_service.create_node(
                                    label=ent_label, 
                                    name=ent_name, 
                                    properties=entity.get("properties", {})
                                )
                                # Link Paper to extracted Concepts
                                await neo4j_service.create_relationship(
                                    source_label="Paper", source_name=doc.title,
                                    target_label=ent_label, target_name=ent_name,
                                    rel_type="REFERENCES"
                                )

                        for rel in relations:
                            s_name = rel.get("source")
                            t_name = rel.get("target")
                            if s_name and t_name:
                                await neo4j_service.create_relationship(
                                    source_label=rel.get("source_label", "Concept"),
                                    source_name=s_name,
                                    target_label=rel.get("target_label", "Concept"),
                                    target_name=t_name,
                                    rel_type=rel.get("relation", "RELATED_TO"),
                                    properties=rel.get("properties", {})
                                )
                    except Exception as chunk_exc:
                        logger.error(f"[Stage 6 Error] Failed to extract or store knowledge for chunk {chunk.id}: {chunk_exc}")
                        continue
                
                # Optional: slight delay between batches to respect rate limits
                import asyncio
                await asyncio.sleep(1)

            logger.info(f"STATUS UPDATE: Setting COMPLETED status for doc_id {document_id}")
            doc.status = IngestionStatus.COMPLETED
            await db.commit()
            logger.info(f"UPLOAD_COMPLETED: Ingestion completed for document_id: {document_id}")

        except Exception as e:
            user_id = doc.uploaded_by if 'doc' in locals() and doc else "Unknown"
            logger.error(f"Error during ingestion execution for doc {document_id} [user_id={user_id}, type={type(e).__name__}]: {e}", exc_info=True)
            await db.rollback()
            try:
                # Re-fetch document cleanly to mark as failed
                result = await db.execute(select(Document).where(Document.id == document_id))
                doc_to_fail = result.scalars().first()
                if doc_to_fail:
                    doc_to_fail.status = IngestionStatus.FAILED
                    doc_to_fail.error_message = str(e)[:500]
                    await db.commit()
            except Exception as rollback_exc:
                logger.error(f"Critical failure while marking document {document_id} as FAILED: {rollback_exc}")
