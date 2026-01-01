import asyncio
import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from rag_agent.agents.retrieval_tool import retrieval_tool

async def test_retrieval():
    print("Testing Qdrant connection...")
    try:
        result = await retrieval_tool.retrieve_context('test', top_k=1)
        print(f'Retrieved {len(result)} chunks')
        print("Test completed successfully")
        return result
    except Exception as e:
        print(f"Error during retrieval: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    results = asyncio.run(test_retrieval())