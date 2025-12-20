#!/usr/bin/env python3
"""
Test script to understand the return type of Qdrant's query_points method
"""
import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Load environment variables
load_dotenv()

def test_query_return_type():
    """Test what type of object query_points returns"""
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "ragchtbot_embadding")

    if not qdrant_url or not qdrant_api_key:
        print("QDRANT_URL and QDRANT_API_KEY must be set in .env file")
        return

    client = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_api_key,
        prefer_grpc=False
    )

    # Use a simple test query (zeros vector) to see what comes back
    test_embedding = [0.0] * 1024  # 1024-dimensional zero vector

    try:
        print("Testing query_points method...")
        result = client.query_points(
            collection_name=collection_name,
            query=test_embedding,
            limit=1,
            with_payload=True
        )

        print(f"Type of result: {type(result)}")
        print(f"Result attributes: {dir(result)}")

        # Check what attribute contains the points
        points = getattr(result, 'points', None)
        if points is not None:
            print(f"Type of result.points: {type(points)}")
            print(f"Length of points: {len(points) if hasattr(points, '__len__') else 'N/A'}")

            if points and len(points) > 0:
                first_item = points[0]
                print(f"Type of first item: {type(first_item)}")
                print(f"First item attributes: {dir(first_item)}")
                print(f"First item: {first_item}")

                # Check if it has the expected attributes
                print(f"Has 'payload': {hasattr(first_item, 'payload')}")
                print(f"Has 'id': {hasattr(first_item, 'id')}")
                print(f"Has 'score': {hasattr(first_item, 'score')}")

                if hasattr(first_item, 'payload'):
                    print(f"Payload type: {type(first_item.payload)}")
                    print(f"Payload: {first_item.payload}")

                if hasattr(first_item, 'id'):
                    print(f"ID: {first_item.id}")

                if hasattr(first_item, 'score'):
                    print(f"Score: {first_item.score}")
        else:
            print("No 'points' attribute found in result")
            # Try other common attributes
            for attr in ['result', 'hits', 'data', 'documents']:
                if hasattr(result, attr):
                    print(f"Found '{attr}' attribute: {getattr(result, attr)}")

    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_query_return_type()