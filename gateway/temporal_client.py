"""
Temporal Client Singleton

Manages connection to Temporal Cloud for workflow execution.
"""

import os
from typing import Optional
from temporalio.client import Client


class TemporalClientManager:
    """Singleton manager for Temporal client"""

    _instance: Optional[Client] = None
    _initialized: bool = False

    @classmethod
    async def get_client(cls) -> Client:
        """
        Get or create Temporal client

        Returns:
            Connected Temporal client
        """
        if cls._instance is not None:
            return cls._instance

        # Get configuration from environment
        temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
        temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
        temporal_api_key = os.getenv("TEMPORAL_API_KEY")

        # Connect to Temporal Cloud
        if temporal_api_key:
            # Cloud connection with API key and TLS
            cls._instance = await Client.connect(
                temporal_address,
                namespace=temporal_namespace,
                api_key=temporal_api_key,
                tls=True,  # Enable TLS for Temporal Cloud
            )
        else:
            # Local Temporal server (no TLS)
            cls._instance = await Client.connect(
                temporal_address,
                namespace=temporal_namespace,
            )

        cls._initialized = True
        return cls._instance

    @classmethod
    async def close(cls):
        """Close the Temporal client connection"""
        if cls._instance is not None:
            await cls._instance.close()
            cls._instance = None
            cls._initialized = False
