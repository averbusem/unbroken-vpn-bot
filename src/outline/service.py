import logging
from typing import Dict, Optional

import backoff
from pyoutlineapi import AsyncOutlineClient, DataLimit
from pyoutlineapi import exceptions as outline_exceptions

from src.config import settings

logger = logging.getLogger(__name__)


class OutlineManager:
    """
    Production-ready manager for Outline VPN keys using the pyoutlineapi library.

    Handles creation, deletion, and listing of access keys with retry logic,
    TLS fingerprint verification, and optional data limits.
    Ensures proper client session management via context manager.
    """

    def __init__(self):
        self._api_url: str = settings.OUTLINE_API_URL
        self._cert: str = settings.OUTLINE_CERT_SHA256

    @backoff.on_exception(backoff.expo, outline_exceptions.OutlineError, max_time=60)
    async def create_key(
        self,
        name: str,
        data_limit_gb: Optional[int] = None,
    ) -> Dict[str, str]:
        """
        Create a new access key with an optional data limit (in GB).
        Uses context manager to ensure client session is opened and closed correctly.
        """
        limit = DataLimit(bytes=data_limit_gb * 1024**3) if data_limit_gb else None
        try:
            async with AsyncOutlineClient(
                api_url=self._api_url,
                cert_sha256=self._cert,
                enable_logging=False,
            ) as client:
                key = await client.create_access_key(name=name, limit=limit)
            logger.info("Created Outline key %s for name=%s", key.id, name)
            return {"id": key.id, "accessUrl": key.access_url}
        except outline_exceptions.OutlineError as e:
            logger.error("Failed to create Outline key for %s: %s", name, e)
            raise

    @backoff.on_exception(backoff.expo, outline_exceptions.OutlineError, max_time=60)
    async def delete_key(self, key_id: str) -> None:
        """
        Delete an existing access key by its ID.
        Ensures client session is closed after deletion.
        """
        try:
            async with AsyncOutlineClient(
                api_url=self._api_url,
                cert_sha256=self._cert,
                enable_logging=False,
            ) as client:
                await client.delete_access_key(key_id)
            logger.info("Deleted Outline key %s", key_id)
        except outline_exceptions.OutlineError as e:
            logger.error("Failed to delete Outline key %s: %s", key_id, e)
            raise

    @backoff.on_exception(backoff.expo, outline_exceptions.OutlineError, max_time=60)
    async def list_keys(self) -> Dict[str, any]:
        """
        List all access keys on the Outline server.
        """
        try:
            async with AsyncOutlineClient(
                api_url=self._api_url,
                cert_sha256=self._cert,
                enable_logging=False,
            ) as client:
                keys = await client.get_access_keys()
            logger.debug("Fetched %d Outline keys", len(keys.access_keys))
            return {
                "total": keys.total,
                "accessKeys": [
                    {"id": k.id, "name": k.name, "accessUrl": k.access_url}
                    for k in keys.access_keys
                ],
            }
        except outline_exceptions.OutlineError as e:
            logger.error("Failed to list Outline keys: %s", e)
            raise

    @backoff.on_exception(backoff.expo, outline_exceptions.OutlineError, max_time=60)
    async def get_server_info(self) -> Dict[str, any]:
        """
        Retrieve server metadata such as version and health status.
        """
        try:
            async with AsyncOutlineClient(
                api_url=self._api_url,
                cert_sha256=self._cert,
                enable_logging=False,
            ) as client:
                info = await client.get_server_info()
            logger.info("Connected to Outline server %s v%s", info.name, info.version)
            return info.dict()
        except outline_exceptions.OutlineError as e:
            logger.error("Failed to get Outline server info: %s", e)
            raise
