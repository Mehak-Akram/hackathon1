"""
Connection pooling utilities for external services in the RAG Agent Service
"""
from typing import Optional, Dict, Any
import asyncio
from contextlib import asynccontextmanager
import httpx
from ..config.settings import settings


class ConnectionPool:
    """
    Connection pool manager for external services like OpenAI and Qdrant
    """
    def __init__(self):
        self._pools: Dict[str, Any] = {}
        self._initialized = False

    async def initialize(self):
        """
        Initialize connection pools for external services
        """
        if self._initialized:
            return

        # Create HTTP client pool for external API calls
        self._pools['http'] = httpx.AsyncClient(
            timeout=settings.response_timeout_seconds,
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=settings.max_concurrent_requests
            )
        )

        self._initialized = True

    async def get_http_client(self) -> httpx.AsyncClient:
        """
        Get the shared HTTP client for external API calls
        """
        if not self._initialized:
            await self.initialize()
        return self._pools['http']

    async def close(self):
        """
        Close all connection pools
        """
        for client in self._pools.values():
            if hasattr(client, 'aclose'):
                await client.aclose()
        self._pools.clear()
        self._initialized = False


# Global connection pool instance
connection_pool = ConnectionPool()


@asynccontextmanager
async def get_http_client():
    """
    Context manager to get an HTTP client from the pool
    """
    client = await connection_pool.get_http_client()
    try:
        yield client
    finally:
        # httpx clients are typically long-lived, so we don't close them here
        # The connection pool manages the lifecycle
        pass


# Initialize the connection pool when module is imported
async def init_connection_pool():
    """
    Initialize the connection pool
    """
    await connection_pool.initialize()


# Initialize the connection pool lazily when first needed
# This avoids issues with event loops during import
# The initialization will happen when get_http_client is first called