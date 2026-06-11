import asyncio
from app.agents.orchestrator import orchestrator
from app.services.chroma_service import chroma_service

async def main():
    print("Testing Chroma Search")
    res = await chroma_service.search_chunks("BERT", limit=2)
    print("Search Results:", res)
    
    print("Testing Orchestrator")
    out = await orchestrator.execute_query("What is BERT?")
    print("Orchestrator Out:", out)

if __name__ == "__main__":
    asyncio.run(main())
