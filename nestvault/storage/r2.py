"""Cloudflare R2 storage adapter (S3-compatible)."""

from nestvault.config import S3Config
from nestvault.logging import get_logger
from nestvault.storage.s3 import S3StorageAdapter

logger = get_logger("storage.r2")


class R2StorageAdapter(S3StorageAdapter):
    """Storage adapter for Cloudflare R2 (S3-compatible).

    R2 uses the same API as S3, so this adapter extends S3StorageAdapter
    with the custom endpoint URL configured.
    """

    def __init__(self, config: S3Config):
        """Initialize the R2 storage adapter.

        Args:
            config: S3-compatible configuration with R2 endpoint

        Raises:
            ValueError: If endpoint is not configured
        """
        if not config.endpoint:
            raise ValueError("R2 requires S3_ENDPOINT to be configured")

        logger.debug(f"Initializing R2 adapter with endpoint: {config.endpoint}")
        super().__init__(config)
