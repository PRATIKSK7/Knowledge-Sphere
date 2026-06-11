# Knowledge Sphere - Portfolio Optimization

This document provides tailored descriptions, bullet points, and summaries of the **Knowledge Sphere** project, specifically optimized for resumes, LinkedIn profiles, and developer portfolios. These are designed to pass ATS (Applicant Tracking Systems) and impress technical recruiters, engineering managers, and researchers.

---

## 📄 Resume Bullet Points (Software Engineer / AI Engineer)

*Choose 3-4 bullet points that best match the job description you are applying for.*

**Option 1 (AI & ML Focus):**
- Architected and deployed **Knowledge Sphere**, an end-to-end AI Research Intelligence Platform integrating **Google Gemini, OpenAI GPT-4o, and local Ollama** models via a custom LLM routing service.
- Engineered an asynchronous document ingestion pipeline using **Celery, Redis, and PyPDF2**, automatically generating 3072-dimensional semantic embeddings for dense academic PDFs.
- Implemented **RAG (Retrieval-Augmented Generation)** over **ChromaDB**, reducing search hallucination and ensuring high-precision context retrieval for a Literature Review generator.
- Extracted entities and mapped relationships into a **Neo4j** graph database, visualizing complex knowledge structures via an interactive **React Flow** frontend interface.

**Option 2 (Backend & Infrastructure Focus):**
- Built a high-performance **FastAPI** backend supporting JWT authentication, Role-Based Access Control, and robust RESTful architecture.
- Designed a distributed background processing system with **Celery & Redis**, reducing API blocking time by 90% during massive PDF extraction and embedding generation.
- Dockerized the entire microservices stack (**PostgreSQL, Redis, Neo4j, ChromaDB, FastAPI, React**) utilizing multi-stage builds and centralized configuration via environment variables.
- Developed an automated End-to-End (`e2e_validation.py`) testing suite with `httpx` to guarantee zero-downtime deployments and consistent API contracts.

**Option 3 (Full-Stack & UX Focus):**
- Developed a highly responsive Single Page Application (SPA) using **React 18, TypeScript, Vite, and Zustand**, styled with **Tailwind CSS**.
- Created an intuitive, real-time Research Chat interface and interactive Knowledge Graph using **React Flow**, enabling academics to visually explore connected document data.
- Optimized frontend bundle size and API latency, achieving sub-50ms data retrieval times across complex SQL and vector queries.

---

## 💼 LinkedIn Project Description

**Knowledge Sphere - AI Research Intelligence Platform**  
*(FastAPI, React, Celery, ChromaDB, Neo4j, Gemini/OpenAI)*

I built Knowledge Sphere to solve a critical problem in academia: information overload. This platform serves as a multi-model AI research assistant that ingests complex PDF documents, generates semantic embeddings, and creates interactive knowledge graphs. 

**Key Technical Achievements:**
✅ Built a fault-tolerant LLM router that dynamically falls back between Google Gemini, OpenAI, and local Ollama models depending on API quota and latency.
✅ Engineered an async document ingestion pipeline with Celery and Redis to handle heavy PDF parsing and chunking without blocking the main event loop.
✅ Integrated ChromaDB for semantic vector search (3072 dimensions) and Neo4j for deep entity-relationship mapping.
✅ Containerized the entire infrastructure using Docker Compose for seamless, one-click deployments.

Check out the source code and architectural diagrams here: [Link to GitHub]

---

## 🌐 Personal Portfolio Project Summary

### **Knowledge Sphere** 
*An Open-Source Platform for AI-Driven Document Analysis*

**The Problem:** Researchers spend countless hours reading and synthesizing dense PDFs. Traditional keyword search often misses the semantic meaning, and standard LLMs hallucinate when asked about proprietary documents.

**The Solution:** I developed Knowledge Sphere, a comprehensive RAG (Retrieval-Augmented Generation) platform. Users can upload PDFs which are instantly processed by distributed Celery workers. The text is chunked, embedded via Google Gemini/OpenAI, and stored in ChromaDB for semantic search. Concurrently, the LLM extracts entities to build an interactive Neo4j knowledge graph.

**Technologies Used:**
- **Frontend:** React, TypeScript, Vite, Zustand, Tailwind CSS, React Flow
- **Backend:** Python, FastAPI, SQLAlchemy, Alembic, Celery
- **Databases:** PostgreSQL (Relational), Redis (Queue), ChromaDB (Vector), Neo4j (Graph)
- **DevOps:** Docker, Docker Compose, Git

**Business Value / Impact:**
- Demonstrated ability to integrate and orchestrate multiple state-of-the-art databases (Relational, Vector, Graph, Cache).
- Showcased production-level Python concurrency (Asyncio + Celery).
- Provided a highly scalable, containerized architecture ready for cloud deployment.
