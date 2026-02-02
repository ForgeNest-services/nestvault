"""Storage adapters for different storage backends."""

from nestvault.storage.base import StorageAdapter
from nestvault.storage.s3 import S3StorageAdapter
from nestvault.storage.backblaze import BackblazeStorageAdapter
from nestvault.storage.r2 import R2StorageAdapter

__all__ = [
    "StorageAdapter",
    "S3StorageAdapter",
    "BackblazeStorageAdapter",
    "R2StorageAdapter",
]
