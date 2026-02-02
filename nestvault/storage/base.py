"""Abstract base class for storage adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class StorageObject:
    """Represents an object in storage."""

    key: str
    size: int
    last_modified: datetime


class StorageAdapter(ABC):
    """Abstract base class for storage adapters."""

    @abstractmethod
    def upload(self, local_path: Path, remote_key: str) -> None:
        """Upload a file to storage.

        Args:
            local_path: Path to the local file
            remote_key: Key/path in the storage bucket

        Raises:
            StorageError: If the upload fails
        """
        pass

    @abstractmethod
    def list(self, prefix: str = "") -> list[StorageObject]:
        """List objects in storage with optional prefix filter.

        Args:
            prefix: Filter objects by key prefix

        Returns:
            List of StorageObject instances

        Raises:
            StorageError: If listing fails
        """
        pass

    @abstractmethod
    def delete(self, remote_key: str) -> None:
        """Delete an object from storage.

        Args:
            remote_key: Key/path of the object to delete

        Raises:
            StorageError: If deletion fails
        """
        pass

    @abstractmethod
    def delete_many(self, remote_keys: list[str]) -> None:
        """Delete multiple objects from storage.

        Args:
            remote_keys: List of keys to delete

        Raises:
            StorageError: If deletion fails
        """
        pass
