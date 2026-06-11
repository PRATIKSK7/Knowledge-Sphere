#!/usr/bin/env python3
"""
Knowledge Sphere — End-to-End Production Validation
====================================================
Tests the complete pipeline: Register → Login → Upload → Parse → Embed → Search → Chat
"""
import asyncio
import sys
import time
import httpx

API_BASE = "http://localhost:8000/api/v1"

# ANSI colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

passed = 0
failed = 0

def check(label: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  {GREEN}✓{RESET} {label}")
    else:
        failed += 1
        print(f"  {RED}✗{RESET} {label} — {detail}")


SAMPLE_TEXT = """
BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding

Jacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova
Google AI Language

Abstract
We introduce a new language representation model called BERT, which stands for
Bidirectional Encoder Representations from Transformers. Unlike recent language
representation models, BERT is designed to pre-train deep bidirectional
representations from unlabeled text by jointly conditioning on both left and right
context in all layers. As a result, the pre-trained BERT model can be fine-tuned
with just one additional output layer to create state-of-the-art models for a
wide range of tasks, such as question answering and language inference, without
substantial task-specific architecture modifications.

BERT is conceptually simple and empirically powerful. It obtains new
state-of-the-art results on eleven natural language processing benchmarks,
including pushing the GLUE score to 80.5% (7.7% point absolute improvement),
MultiNLI accuracy to 86.7% (4.6% absolute improvement), SQuAD v1.1 question
answering Test F1 to 93.2 (1.5 point absolute improvement) and SQuAD v2.0 Test
F1 to 83.1 (5.1 point absolute improvement).

Keywords: BERT, Transformers, NLP, Pre-training, Language Understanding, Masked Language Model, Next Sentence Prediction

1. Introduction
Language model pre-training has been shown to be effective for improving many
natural language processing tasks. These include sentence-level tasks such as
natural language inference and paraphrasing, which aim to predict the
relationships between sentences by analyzing them holistically, as well as
token-level tasks such as named entity recognition and question answering,
where models are required to produce fine-grained output at the token level.

There are two existing strategies for applying pre-trained language
representations to downstream tasks: feature-based and fine-tuning. The
feature-based approach, such as ELMo, uses task-specific architectures that
include the pre-trained representations as additional features. The fine-tuning
approach, such as the Generative Pre-trained Transformer (OpenAI GPT),
introduces minimal task-specific parameters, and is trained on the downstream
tasks by simply fine-tuning all pre-trained parameters.

2. BERT Model Architecture
BERT's model architecture is a multi-layer bidirectional Transformer encoder
based on the original implementation described in Vaswani et al. (2017). We
denote the number of layers (i.e., Transformer blocks) as L, the hidden size as
H, and the number of self-attention heads as A. We primarily report results on
two model sizes: BERT-BASE (L=12, H=768, A=12, Total Parameters=110M) and
BERT-LARGE (L=24, H=1024, A=16, Total Parameters=340M).

3. Pre-training Procedure
BERT uses two unsupervised tasks for pre-training:
- Masked Language Modeling (MLM): Randomly mask some percentage of the input
  tokens and then predict those masked tokens. This allows the representation
  to fuse the left and the right context.
- Next Sentence Prediction (NSP): Given two sentences A and B, predict whether
  B is the actual next sentence that follows A, or a random sentence.

References
[1] Vaswani, A., Shazeer, N., Parmar, N., et al. Attention is all you need. NIPS 2017.
[2] Devlin, J., Chang, M.-W., Lee, K., Toutanova, K. BERT: Pre-training of Deep Bidirectional Transformers. 2019.
[3] Peters, M., Neumann, M., et al. Deep contextualized word representations. NAACL-HLT 2018.
"""


async def run_validation():
    global passed, failed

    print(f"\n{BOLD}{CYAN}{'=' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  KNOWLEDGE SPHERE — E2E PRODUCTION VALIDATION{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 60}{RESET}\n")

    # ─── Phase 1: Health Checks ───────────────────────────────
    print(f"{BOLD}Phase 1: Health Checks{RESET}")
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            r = await client.get("http://localhost:8000/health")
            check("Backend /health", r.status_code == 200, f"HTTP {r.status_code}")

            r = await client.get(f"{API_BASE}/health/chroma")
            check("ChromaDB health", r.status_code == 200, f"HTTP {r.status_code}")
    except Exception as e:
        check("Health checks reachable", False, str(e))
        print(f"\n{RED}Backend unreachable. Aborting.{RESET}")
        return

    # ─── Phase 2: Authentication ──────────────────────────────
    print(f"\n{BOLD}Phase 2: Authentication{RESET}")
    headers = {}
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Try login first
            r = await client.post(
                f"{API_BASE}/auth/login",
                data={"username": "e2e_prod@test.com", "password": "TestPass123!"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if r.status_code != 200:
                # Register
                reg = await client.post(
                    f"{API_BASE}/auth/register",
                    json={
                        "email": "e2e_prod@test.com",
                        "password": "TestPass123!",
                        "full_name": "E2E Production Tester",
                    },
                )
                check("Register user", reg.status_code == 201, f"HTTP {reg.status_code}: {reg.text[:200]}")
                r = await client.post(
                    f"{API_BASE}/auth/login",
                    data={"username": "e2e_prod@test.com", "password": "TestPass123!"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

            check("Login", r.status_code == 200, f"HTTP {r.status_code}")
            token = r.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Verify /me
            me = await client.get(f"{API_BASE}/auth/me", headers=headers)
            check("GET /auth/me", me.status_code == 200, f"HTTP {me.status_code}")
    except Exception as e:
        check("Authentication flow", False, str(e))
        print(f"\n{RED}Auth failed. Aborting.{RESET}")
        return

    # ─── Phase 3: Document Upload ─────────────────────────────
    print(f"\n{BOLD}Phase 3: Document Upload{RESET}")
    doc_id = None
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            r = await client.post(
                f"{API_BASE}/documents/upload",
                headers=headers,
                files={"file": ("bert_paper.txt", SAMPLE_TEXT.encode(), "text/plain")},
            )
            check("Upload document", r.status_code in (200, 201), f"HTTP {r.status_code}: {r.text[:200]}")
            if r.status_code in (200, 201):
                doc_id = r.json()["id"]
                print(f"    Document ID: {doc_id}")
    except Exception as e:
        check("Upload", False, str(e))

    if not doc_id:
        print(f"\n{RED}Upload failed. Aborting.{RESET}")
        return

    # ─── Phase 4: Document Lifecycle Tracking ─────────────────
    print(f"\n{BOLD}Phase 4: Document Ingestion Pipeline{RESET}")
    final_status = "pending"
    seen_states = set()
    async with httpx.AsyncClient(timeout=300.0) as client:
        for attempt in range(60):  # Up to 2 minutes
            r = await client.get(f"{API_BASE}/documents/{doc_id}", headers=headers)
            if r.status_code == 200:
                status = r.json()["status"]
                if status not in seen_states:
                    seen_states.add(status)
                    print(f"    → {status}")
                final_status = status
                if status in ("completed", "failed"):
                    break
            await asyncio.sleep(2)

    check("Ingestion completed", final_status == "completed", f"Final status: {final_status}")
    if final_status == "failed":
        async with httpx.AsyncClient(timeout=300.0) as client:
            r = await client.get(f"{API_BASE}/documents/{doc_id}", headers=headers)
            err = r.json().get("error_message", "unknown")
            print(f"    {RED}Error: {err}{RESET}")

    # ─── Phase 5: Semantic Search ─────────────────────────────
    print(f"\n{BOLD}Phase 5: Semantic Search (Vector DB){RESET}")
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            r = await client.get(
                f"{API_BASE}/search/semantic",
                params={"query": "What is BERT?", "limit": 5},
                headers=headers,
            )
            check("Semantic search API", r.status_code == 200, f"HTTP {r.status_code}: {r.text[:200]}")
            if r.status_code == 200:
                chunks = r.json()
                check("Returns chunks", len(chunks) > 0, f"Got {len(chunks)} chunks")
                if chunks:
                    content = " ".join(c["content"] for c in chunks).lower()
                    check("Contains 'bidirectional'", "bidirectional" in content)
                    check("Contains 'transformer'", "transformer" in content)
                    check("Has confidence scores", all("confidence" in c for c in chunks))
                    check("Has metadata", all("metadata" in c for c in chunks))
                    # Verify document_id is present and consistent
                    doc_ids_in_results = set(c["metadata"].get("document_id") for c in chunks)
                    check("document_id in metadata", all(c["metadata"].get("document_id") is not None for c in chunks))
                    print(f"    Returned doc_ids: {doc_ids_in_results}")
    except Exception as e:
        check("Semantic search", False, f"{type(e).__name__}: {e}")

    # ─── Phase 6: Research Chat ───────────────────────────────
    print(f"\n{BOLD}Phase 6: Research Chat (RAG Pipeline){RESET}")
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            r = await client.post(
                f"{API_BASE}/search/chat",
                headers=headers,
                json={"query": "What is BERT and how does it work?"},
            )
            check("Chat API responds", r.status_code == 200, f"HTTP {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                check("Has answer field", bool(data.get("answer")))
                check("Has citations", len(data.get("citations", [])) > 0)
                check("Has confidence_score", "confidence_score" in data)
                # Answer should reference BERT context
                answer = data.get("answer", "").lower()
                check("Answer references BERT content", 
                      "bert" in answer or "bidirectional" in answer or "transformer" in answer or "retrieved" in answer,
                      f"Answer preview: {data.get('answer', '')[:100]}")
    except Exception as e:
        check("Research Chat", False, str(e))

    # ─── Phase 7: Knowledge Graph ─────────────────────────────
    print(f"\n{BOLD}Phase 7: Knowledge Graph{RESET}")
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            r = await client.get(f"{API_BASE}/graph/data", headers=headers)
            check("Graph data API", r.status_code == 200, f"HTTP {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                check("Has nodes key", "nodes" in data)
                check("Has links key", "links" in data)
    except Exception as e:
        check("Knowledge Graph", False, str(e))

    # ─── Phase 8: Research Gaps ───────────────────────────────
    print(f"\n{BOLD}Phase 8: Research Gaps{RESET}")
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            r = await client.get(f"{API_BASE}/graph/gaps", headers=headers)
            check("Research gaps API", r.status_code == 200, f"HTTP {r.status_code}")
    except Exception as e:
        check("Research Gaps", False, str(e))

    # ─── Phase 9: Analytics Dashboard ─────────────────────────
    print(f"\n{BOLD}Phase 9: Analytics Dashboard{RESET}")
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            r = await client.get(f"{API_BASE}/analytics/", headers=headers)
            check("Analytics API", r.status_code == 200, f"HTTP {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                check("Has total_documents", "total_documents" in data)
                check("Has graph stats", "graph" in data)
                check("total_documents >= 1", data.get("total_documents", 0) >= 1)
    except Exception as e:
        check("Analytics", False, str(e))

    # ─── Phase 10: Document List ──────────────────────────────
    print(f"\n{BOLD}Phase 10: Document Management{RESET}")
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            r = await client.get(f"{API_BASE}/documents/", headers=headers)
            check("List documents API", r.status_code == 200, f"HTTP {r.status_code}")
            if r.status_code == 200:
                docs = r.json()
                check("Has at least 1 document", len(docs) >= 1, f"Found {len(docs)}")
    except Exception as e:
        check("Document Management", False, str(e))

    # ─── Summary ──────────────────────────────────────────────
    total = passed + failed
    print(f"\n{BOLD}{CYAN}{'=' * 60}{RESET}")
    print(f"{BOLD}  RESULTS: {GREEN}{passed} passed{RESET}, {RED}{failed} failed{RESET} out of {total} checks")
    if failed == 0:
        print(f"{BOLD}{GREEN}  ✓ ALL CHECKS PASSED — PLATFORM IS PRODUCTION READY{RESET}")
    else:
        print(f"{BOLD}{YELLOW}  ⚠ {failed} issue(s) need attention{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 60}{RESET}\n")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_validation())
    sys.exit(0 if success else 1)
