import logging
from typing import Dict, Any, List
from app.services.chroma_service import chroma_service
from app.services.neo4j_service import neo4j_service
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class AgentState:
    def __init__(self, query: str, history: List[Dict[str, str]] = None):
        self.query = query
        self.history = history or []
        self.retrieved_chunks = []
        self.entities = []
        self.relationships = []
        self.graph_paths = []
        self.analysis = ""
        self.citations = []
        self.report = ""
        self.confidence_score = 0.85

class ResearchAgent:
    async def run(self, state: AgentState):
        logger.info(f"Research Agent searching context for query: {state.query}")
        results = await chroma_service.search_chunks(state.query, limit=4)
        logger.info(f"RETRIEVAL_COMPLETED: Retrieved {len(results)} chunks")
        state.retrieved_chunks = results
        # Compute confidence based on top search matches
        if results:
            state.confidence_score = sum(r["confidence"] for r in results) / len(results)
        else:
            state.confidence_score = 0.5

class KnowledgeAgent:
    async def run(self, state: AgentState):
        logger.info("Knowledge Agent extracting entities and relations from retrieved documents.")
        all_text = "\n\n".join([chunk["content"] for chunk in state.retrieved_chunks])
        if not all_text:
            return
        # Avoid processing huge chunks if too large
        truncated_text = all_text[:4000]
        try:
            extracted = await LLMService.extract_knowledge(truncated_text)
            state.entities = extracted.get("entities", [])
            state.relationships = extracted.get("relationships", [])
        except Exception as e:
            logger.warning(f"Knowledge extraction failed (LLM unavailable?): {e}")
            state.entities = []
            state.relationships = []

class GraphAgent:
    async def run(self, state: AgentState):
        logger.info("Graph Agent writing extracted entities and relations to Neo4j.")
        for entity in state.entities:
            try:
                await neo4j_service.create_node(
                    label=entity.get("label", "Concept"),
                    name=entity.get("name", "Unknown"),
                    properties=entity.get("properties", {})
                )
            except Exception as e:
                logger.error(f"GraphAgent failed to create node {entity.get('name')}: {e}")

        for rel in state.relationships:
            try:
                await neo4j_service.create_relationship(
                    source_label=rel.get("source_label", "Concept"),
                    source_name=rel.get("source"),
                    target_label=rel.get("target_label", "Concept"),
                    target_name=rel.get("target"),
                    rel_type=rel.get("relation", "RELATED_TO"),
                    properties=rel.get("properties", {})
                )
            except Exception as e:
                logger.error(f"GraphAgent failed to create relationship: {e}")
            
        # Traverse paths (Module 10)
        if len(state.entities) >= 2:
            try:
                paths = await neo4j_service.find_connecting_paths(
                    source=state.entities[0]["name"],
                    target=state.entities[-1]["name"]
                )
                state.graph_paths = paths
            except Exception as e:
                logger.error(f"GraphAgent path traversal failed: {e}")

class ReasoningAgent:
    async def run(self, state: AgentState):
        logger.info("Reasoning Agent analyzing graph paths and retrieved context.")
        context_str = "\n".join([c["content"] for c in state.retrieved_chunks])
        if not context_str.strip():
            state.analysis = "No relevant documents found for this query."
            return

        paths_str = ""
        if state.graph_paths:
            paths_str = "\n".join([f"Path: {' -> '.join(p.get('path_sequence', []))}" for p in state.graph_paths])
            
        history_str = ""
        if state.history:
            history_str = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in state.history])
            
        prompt = f"""
        Analyze the query: "{state.query}"
        
        Previous Conversation History:
        ---
        {history_str}
        ---
        
        Use the retrieved context text:
        ---
        {context_str}
        ---
        
        And the knowledge graph path connections:
        ---
        {paths_str}
        ---
        
        Generate a multi-hop causal reasoning answer. Detail connection points between separate nodes/concepts.
        """
        try:
            state.analysis = await LLMService.generate_text(prompt)
        except RuntimeError as e:
            logger.warning(f"ReasoningAgent LLM unavailable: {e}")
            # Provide the raw context as the analysis when LLM is down
            state.analysis = (
                f"**[LLM Unavailable — Raw Retrieved Context]**\n\n"
                f"The following document excerpts were retrieved for your query "
                f"\"{state.query}\":\n\n{context_str[:3000]}"
            )

class CitationAgent:
    async def run(self, state: AgentState):
        logger.info("Citation Agent assigning references to answer.")
        citations = []
        for i, chunk in enumerate(state.retrieved_chunks):
            meta = chunk.get("metadata", {})
            filename = meta.get("filename", f"Doc_{i}")
            doc_id = meta.get("document_id", "Unknown")
            citations.append({
                "citation_key": f"[Source_{i+1}]",
                "document_title": filename,
                "document_id": doc_id,
                "text_snippet": chunk["content"][:200] + "..."
            })
        state.citations = citations

class ReportAgent:
    async def run(self, state: AgentState):
        logger.info("Report Agent formatting and writing the final output.")
        citation_str = "\n".join([f"{c['citation_key']}: {c['document_title']}" for c in state.citations])
        report_prompt = f"""
        Draft a final academic report answering: "{state.query}"
        Based on these reasoning notes:
        {state.analysis}
        
        Incorporate these source citations:
        {citation_str}
        
        Structure with clear sections and citations.
        """
        try:
            state.report = await LLMService.generate_text(report_prompt)
        except RuntimeError as e:
            logger.warning(f"ReportAgent LLM unavailable: {e}")
            # Use analysis as the report fallback
            state.report = state.analysis

class ResearchPlatformOrchestrator:
    def __init__(self):
        self.research_agent = ResearchAgent()
        self.knowledge_agent = KnowledgeAgent()
        self.graph_agent = GraphAgent()
        self.reasoning_agent = ReasoningAgent()
        self.citation_agent = CitationAgent()
        self.report_agent = ReportAgent()

    async def execute_query(self, query: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Execute the agent pipeline sequentially (Module 9 multi-agent architecture).
        
        The pipeline is resilient: if an LLM is not available, semantic search
        results and citations are still returned.  The analysis and report
        fields will contain the raw retrieved context instead.
        """
        state = AgentState(query=query, history=history)
        
        # 1. Retrieve papers (always works — local embeddings)
        await self.research_agent.run(state)
        
        # 2. Extract Entities (gracefully degrades)
        await self.knowledge_agent.run(state)
        
        # 3. Build/Update Knowledge Graph & fetch paths
        await self.graph_agent.run(state)
        
        # 4. Perform reasoning (gracefully degrades)
        await self.reasoning_agent.run(state)
        
        # 5. Extract citations (always works — no LLM needed)
        await self.citation_agent.run(state)
        
        # 6. Compose report (gracefully degrades)
        await self.report_agent.run(state)

        return {
            "query": state.query,
            "answer": state.report,
            "analysis": state.analysis,
            "citations": state.citations,
            "entities": state.entities,
            "relationships": state.relationships,
            "graph_paths": state.graph_paths,
            "confidence_score": round(state.confidence_score, 2)
        }

orchestrator = ResearchPlatformOrchestrator()
