import time
import asyncio
import logging
import numpy as np
import chromadb
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class ChromaService:
    """
    ChromaDB v0.5+ compatible service.

    Key design decisions:
    - HttpClient() is constructed WITHOUT a Settings object — passing Settings
      to HttpClient was removed in chromadb v0.5 and causes tenant validation errors.
    - Connection is lazy and retried up to MAX_RETRIES times with exponential backoff.
    - Collections are always created via get_or_create_collection so the service
      is idempotent across restarts.
    """

    MAX_RETRIES = 5
    RETRY_DELAY = 2  # seconds, doubles each attempt

    def __init__(self):
        self._client = None
        self._doc_collection = None
        self._entity_collection = None

    # ──────────────────────────────────────────────
    # Internal connection helpers
    # ──────────────────────────────────────────────

    def _build_client(self) -> chromadb.HttpClient:
        """
        Create a chromadb.HttpClient pointed at the configured host/port.

        NOTE: Do NOT pass a `settings=` kwarg here — chromadb v0.5 removed
        support for passing Settings to HttpClient, and doing so causes the
        'Could not connect to tenant default_tenant' ValueError.
        """
        host = settings.CHROMA_HOST
        port = settings.CHROMA_PORT
        logger.info(f"[ChromaDB] Initialising HttpClient → http://{host}:{port}")
        client = chromadb.HttpClient(host=host, port=port)
        return client

    def _connect_with_retry(self) -> chromadb.HttpClient:
        """
        Attempt to connect and verify the server heartbeat, retrying on failure.
        """
        delay = self.RETRY_DELAY
        last_error: Exception = RuntimeError("Never attempted")

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                client = self._build_client()
                # heartbeat() raises if the server is unreachable
                hb = client.heartbeat()
                logger.info(f"[ChromaDB] Connected successfully on attempt {attempt}. Heartbeat: {hb}")
                return client
            except Exception as exc:
                last_error = exc
                logger.warning(
                    f"[ChromaDB] Connection attempt {attempt}/{self.MAX_RETRIES} failed: {exc}. "
                    f"Retrying in {delay}s…"
                )
                time.sleep(delay)
                delay = min(delay * 2, 30)

        logger.error(f"[ChromaDB] All {self.MAX_RETRIES} connection attempts failed. Last error: {last_error}")
        raise ConnectionError(
            f"ChromaDB at {settings.CHROMA_HOST}:{settings.CHROMA_PORT} is unreachable "
            f"after {self.MAX_RETRIES} retries. Last error: {last_error}"
        ) from last_error

    # ──────────────────────────────────────────────
    # Lazy properties
    # ──────────────────────────────────────────────

    @property
    def client(self) -> chromadb.HttpClient:
        if self._client is None:
            self._client = self._connect_with_retry()
        return self._client

    @property
    def doc_collection(self):
        if self._doc_collection is None:
            name = settings.CHROMA_COLLECTION_DOCUMENTS
            logger.info(f"[ChromaDB] Getting or creating collection '{name}'")
            self._doc_collection = self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"[ChromaDB] Collection '{name}' ready (count={self._doc_collection.count()})")
        return self._doc_collection

    @property
    def entity_collection(self):
        if self._entity_collection is None:
            name = settings.CHROMA_COLLECTION_ENTITIES
            logger.info(f"[ChromaDB] Getting or creating collection '{name}'")
            self._entity_collection = self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"[ChromaDB] Collection '{name}' ready (count={self._entity_collection.count()})")
        return self._entity_collection

    # ──────────────────────────────────────────────
    # Public health check
    # ──────────────────────────────────────────────

    def health_check(self) -> Dict[str, Any]:
        """
        Verify the ChromaDB server is reachable and return status info.
        Called by GET /health/chroma.
        """
        try:
            hb = self.client.heartbeat()
            logger.info(f"[ChromaDB] Health check OK. Heartbeat: {hb}")
            return {"status": "healthy", "heartbeat": hb}
        except Exception as exc:
            logger.error(f"[ChromaDB] Health check FAILED: {exc}")
            return {"status": "unhealthy", "error": str(exc)}

    # ──────────────────────────────────────────────
    # Embedding generation
    # ──────────────────────────────────────────────

    async def get_embedding(self, text: str, provider: Optional[str] = None) -> List[float]:
        """
        Generate embedding using the global LLMService (Gemini -> OpenAI -> Ollama cascade).
        """
        from app.services.llm_service import LLMService
        return await LLMService.get_embedding(text, provider)

    # ──────────────────────────────────────────────
    # Document chunk operations
    # ──────────────────────────────────────────────

    async def add_chunks(self, document_id: int, chunks: List[Dict[str, Any]]):
        """
        Insert document chunks into ChromaDB.
        chunks: list of {"id": str, "content": str, "metadata": dict}
        """
        logger.info(f"[ChromaDB] Inserting {len(chunks)} chunks for document_id={document_id}")
        ids, documents, embeddings, metadatas = [], [], [], []

        for chunk in chunks:
            ids.append(chunk["id"])
            documents.append(chunk["content"])
            emb = await self.get_embedding(chunk["content"])
            embeddings.append(emb)
            meta = {**chunk.get("metadata", {}), "document_id": document_id}
            metadatas.append(meta)

        collection = self.doc_collection  # resolved synchronously once, before thread
        await asyncio.to_thread(
            collection.add,
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        logger.info(f"[ChromaDB] Successfully inserted {len(ids)} chunks for document_id={document_id}")

    async def search_chunks(
        self,
        query: str,
        limit: int = 5,
        document_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search over document chunks.
        """
        logger.info(f"[ChromaDB] Semantic search: query='{query[:60]}' limit={limit} document_id={document_id}")
        query_emb = await self.get_embedding(query)

        where = {"document_id": document_id} if document_id is not None else None

        collection = self.doc_collection  # resolved synchronously once, before thread
        results = await asyncio.to_thread(
            collection.query,
            query_embeddings=[query_emb],
            n_results=limit,
            where=where
        )

        formatted: List[Dict[str, Any]] = []
        if not results or not results.get("ids") or not results["ids"][0]:
            logger.info("[ChromaDB] Semantic search returned 0 results")
            return formatted

        logger.info(f"retrieved chunk IDs: {results['ids'][0]}")
        if results.get("distances"):
            logger.info(f"similarity scores: {results['distances'][0]}")

        for i in range(len(results["ids"][0])):
            dist = results["distances"][0][i] if results.get("distances") else 0.0
            formatted.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": dist,
                "confidence": max(0.0, min(1.0, 1.0 - dist))
            })

        logger.info(f"[ChromaDB] Semantic search returned {len(formatted)} results")
        return formatted

    async def delete_document_chunks(self, document_id: int):
        """
        Remove all chunks belonging to a document.
        """
        logger.info(f"[ChromaDB] Deleting all chunks for document_id={document_id}")
        collection = self.doc_collection
        await asyncio.to_thread(collection.delete, where={"document_id": document_id})
        logger.info(f"[ChromaDB] Deletion complete for document_id={document_id}")


chroma_service = ChromaService()
