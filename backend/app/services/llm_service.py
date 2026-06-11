import json
import logging
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Production LLM router.

    Provider cascade: preferred provider → Gemini fallback → Ollama fallback.
    If every provider fails, a RuntimeError is raised — no mock data is ever
    returned.
    """

    @classmethod
    async def generate_text(
        cls,
        prompt: str,
        provider: Optional[str] = None,
        json_mode: bool = False,
        stream: bool = False,
    ) -> str:
        """
        Route an LLM generation request through available providers.
        Raises RuntimeError if all providers fail.
        """
        chosen_provider = provider or settings.DEFAULT_LLM_PROVIDER
        errors: List[str] = []
        success = False

        logger.info(f"LLM Routing Start: Preferred provider is '{chosen_provider}'")

        # ── Google Gemini ─────────────────────────────────────────
        # Attempt Gemini if preferred or as fallback, only with a real key
        if (chosen_provider == "gemini" or not success) and settings.is_real_key(settings.GOOGLE_API_KEY):
            if settings.GOOGLE_API_KEY:
                logger.info("Attempting Google Gemini generation...")
                try:
                    url = (
                        f"https://generativelanguage.googleapis.com/v1beta/models/"
                        f"{settings.GEMINI_MODEL}:generateContent?key={settings.GOOGLE_API_KEY}"
                    )
                    payload = {
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.2},
                    }
                    if json_mode:
                        payload["generationConfig"]["responseMimeType"] = "application/json"

                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            url,
                            headers={"Content-Type": "application/json"},
                            json=payload,
                            timeout=300.0,
                        )
                        if response.status_code == 200:
                            success = True
                            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
                        err = f"Gemini HTTP {response.status_code}: {response.text[:300]}"
                        errors.append(err)
                        logger.warning(err)
                except Exception as e:
                    errors.append(f"Gemini exception: {e}")
                    logger.error(f"Gemini text generation failed: {e}")
            else:
                msg = "Gemini requested or fallback attempted, but GOOGLE_API_KEY is not set."
                errors.append(msg)
                logger.warning(msg)

        # ── OpenAI GPT ────────────────────────────────────────────
        # Attempt OpenAI if preferred or as fallback, but only if a real key is set
        if (chosen_provider == "openai" or not success) and settings.is_real_key(settings.OPENAI_API_KEY):
            if settings.OPENAI_API_KEY:
                logger.info("Attempting OpenAI GPT generation...")
                try:
                    headers = {
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    }
                    payload: Dict[str, Any] = {
                        "model": settings.OPENAI_CHAT_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.2,
                        "stream": stream,
                    }
                    if json_mode:
                        payload["response_format"] = {"type": "json_object"}

                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            "https://api.openai.com/v1/chat/completions",
                            headers=headers,
                            json=payload,
                            timeout=300.0,
                        )
                        if response.status_code == 200:
                            success = True
                            return response.json()["choices"][0]["message"]["content"]
                        err = f"OpenAI HTTP {response.status_code}: {response.text[:300]}"
                        errors.append(err)
                        logger.warning(err)
                except Exception as e:
                    errors.append(f"OpenAI exception: {e}")
                    logger.error(f"OpenAI text generation failed: {e}")
            else:
                msg = "OpenAI requested or fallback attempted, but OPENAI_API_KEY is not set."
                errors.append(msg)
                logger.warning(msg)

        # ── Ollama ────────────────────────────────────────────────
        # Attempt Ollama fallback regardless of key (local instance)
        logger.info("Attempting Ollama local generation...")
        try:
            payload = {
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": stream,
                "options": {"temperature": 0.2},
            }
            if json_mode:
                payload["format"] = "json"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json=payload,
                    timeout=300.0,
                )
                if response.status_code == 200:
                    success = True
                    return response.json()["response"]
                err = f"Ollama HTTP {response.status_code}"
                errors.append(err)
                logger.warning(err)
        except Exception as e:
            errors.append(f"Ollama exception: {e}")
            logger.warning(f"Ollama text generation fallback failed: {e}")

        # ── All providers exhausted ───────────────────────────────
        # If all providers failed, provide detailed error summary
        error_summary = " | ".join(errors)
        logger.error(f"All LLM providers failed. Summary: {error_summary}")
        raise RuntimeError(
            f"All LLM providers failed. Please provide a valid OPENAI_API_KEY, GOOGLE_API_KEY, or ensure Ollama is running. Error details: {error_summary}"
        )

    # ─────────────────────────────────────────────────────────────
    # Knowledge extraction (used during document ingestion)
    # ─────────────────────────────────────────────────────────────

    @classmethod
    async def extract_knowledge(cls, text_chunk: str) -> Dict[str, Any]:
        """
        Module 5 & 6: Extract Entities and Relationships from a chunk.

        If no LLM provider is available this returns an empty result so that
        document ingestion can still complete successfully (parsing, chunking,
        and embedding are fully local).  Knowledge extraction will be
        populated retroactively when an LLM becomes available.
        """
        prompt = f"""
        Analyze the text chunk below and extract all entities and their semantic relationships.
        
        Entity categories you can use:
        - People
        - Organizations
        - Locations
        - Concepts
        - Technologies
        - Diseases
        - Events
        - Research Topics
        - Methods
        - Algorithms
        
        Relationship types you can use:
        - RELATED_TO
        - USES
        - DEPENDS_ON
        - CAUSES
        - IMPROVES
        - INVENTED_BY
        - PUBLISHED_BY
        - DEVELOPED_BY
        
        Respond with a JSON object exactly containing two keys: "entities" and "relationships".
        "entities" must be a list of: {{"name": "Entity Name", "label": "Category", "properties": {{ "extra_key": "val" }} }}
        "relationships" must be a list of: {{"source": "Entity Name", "source_label": "Category", "target": "Entity Name", "target_label": "Category", "relation": "RELATION_TYPE", "properties": {{}} }}
        
        Text chunk to process:
        ---
        {text_chunk}
        ---
        """
        try:
            raw_res = await cls.generate_text(prompt, json_mode=True)
        except RuntimeError:
            # No LLM available — skip extraction gracefully
            logger.warning(
                "LLM unavailable for knowledge extraction. "
                "Skipping entity/relationship extraction for this chunk."
            )
            return {"entities": [], "relationships": []}

        try:
            clean_res = raw_res.strip()
            if clean_res.startswith("```json"):
                clean_res = clean_res.split("```json")[1].split("```")[0].strip()
            elif clean_res.startswith("```"):
                clean_res = clean_res.split("```")[1].split("```")[0].strip()
            return json.loads(clean_res)
        except Exception as e:
            logger.error(
                f"Failed to parse JSON in entity extraction: {e}. "
                f"Raw content: {raw_res[:500]}"
            )
            return {"entities": [], "relationships": []}

    # ─────────────────────────────────────────────────────────────
    # Literature review (user-facing, should raise on failure)
    # ─────────────────────────────────────────────────────────────

    @classmethod
    async def generate_literature_review(
        cls, topic: str, context: str, format_style: str = "APA"
    ) -> str:
        prompt = f"""
        Act as an Expert Academic Researcher. Generate a comprehensive literature review on the topic: "{topic}".
        Analyze the following retrieved context papers. DO NOT just summarize them sequentially. Synthesize the findings across multiple documents.
        Format style for citations: {format_style}.
        
        You MUST strictly structure your review with the following exact Markdown headers:
        
        # Literature Review: {topic}
        
        ## Abstract
        Provide a brief summary of the state of the art based on the retrieved documents.
        
        ## Introduction
        Introduce the topic, its significance, and the core themes found across the documents.
        
        ## Key Findings (Multi-Document Synthesis)
        Synthesize the core results and key findings. Group similar findings together and contrast differing results.
        
        ## Methodology Comparison
        Compare and evaluate the different methodologies, datasets, or approaches used by the authors across the provided documents.
        
        ## Research Gaps
        Identify critical structural holes, unsolved problems, and future research directions based on what the literature fails to address.
        
        ## Conclusion
        Generate a cohesive conclusion summarizing the academic landscape of this topic.
        
        Generate proper academic citations inside the text according to {format_style} using the document references provided.
        
        Retrieved context:
        {context}
        """
        return await cls.generate_text(prompt)

    # ─────────────────────────────────────────────────────────────
    # Embeddings generation (used by ChromaService)
    # ─────────────────────────────────────────────────────────────

    @classmethod
    async def get_embedding(cls, text: str, provider: Optional[str] = None) -> List[float]:
        chosen_provider = provider or settings.DEFAULT_EMBEDDING_PROVIDER
        errors = []
        success = False

        if (chosen_provider == "gemini" or not success) and settings.is_real_key(settings.GOOGLE_API_KEY):
            if settings.GOOGLE_API_KEY:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_EMBEDDING_MODEL}:embedContent?key={settings.GOOGLE_API_KEY}"
                    payload = {
                        "model": f"models/{settings.GEMINI_EMBEDDING_MODEL}",
                        "content": {"parts": [{"text": text}]}
                    }
                    async with httpx.AsyncClient() as client:
                        response = await client.post(url, json=payload, timeout=300.0)
                        if response.status_code == 200:
                            success = True
                            return response.json()["embedding"]["values"]
                        errors.append(f"Gemini HTTP {response.status_code}: {response.text[:300]}")
                except Exception as e:
                    errors.append(f"Gemini exception: {e}")
            else:
                errors.append("Gemini requested, but GOOGLE_API_KEY is not set.")

        if (chosen_provider == "openai" or not success) and settings.is_real_key(settings.OPENAI_API_KEY):
            if settings.OPENAI_API_KEY:
                try:
                    url = "https://api.openai.com/v1/embeddings"
                    headers = {
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": settings.OPENAI_EMBEDDING_MODEL,
                        "input": text
                    }
                    async with httpx.AsyncClient() as client:
                        response = await client.post(url, headers=headers, json=payload, timeout=300.0)
                        if response.status_code == 200:
                            success = True
                            return response.json()["data"][0]["embedding"]
                        errors.append(f"OpenAI HTTP {response.status_code}: {response.text[:300]}")
                except Exception as e:
                    errors.append(f"OpenAI exception: {e}")
            else:
                errors.append("OpenAI requested, but OPENAI_API_KEY is not set.")

        # Ollama Fallback
        try:
            url = f"{settings.OLLAMA_BASE_URL}/api/embeddings"
            payload = {
                "model": settings.OLLAMA_EMBEDDING_MODEL,
                "prompt": text
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=300.0)
                if response.status_code == 200:
                    success = True
                    return response.json()["embedding"]
                errors.append(f"Ollama HTTP {response.status_code}")
        except Exception as e:
            errors.append(f"Ollama exception: {e}")

        raise RuntimeError(f"All embedding providers failed: {' | '.join(errors)}")
