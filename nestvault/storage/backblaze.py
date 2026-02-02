"""Backblaze B2 storage adapter using b2sdk."""

from pathlib import Path

from b2sdk.v2 import B2Api, InMemoryAccountInfo
from b2sdk.v2.exception import B2Error

from nestvault.config import BackblazeConfig
from nestvault.exceptions import StorageError
from nestvault.logging import get_logger
from nestvault.storage.base import StorageAdapter, StorageObject

logger = get_logger("storage.backblaze")


class BackblazeStorageAdapter(StorageAdapter):
    """Storage adapter for Backblaze B2."""

    def __init__(self, config: BackblazeConfig):
        """Initialize the Backblaze B2 storage adapter.

        Args:
            config: Backblaze B2 configuration
        """
        self.config = config

        try:
            info = InMemoryAccountInfo()
            self.api = B2Api(info)
            self.api.authorize_account("production", config.key_id, config.application_key)
            self.bucket = self.api.get_bucket_by_name(config.bucket)
            logger.debug(f"Initialized B2 client for bucket '{config.bucket}'")
        except B2Error as e:
            logger.error(f"Failed to initialize B2 client: {e}")
            raise StorageError(f"Failed to initialize Backblaze B2: {e}")

    def upload(self, local_path: Path, remote_key: str) -> None:
        """Upload a file to Backblaze B2.

        Args:
            local_path: Path to the local file
            remote_key: Key/path in the B2 bucket

        Raises:
            StorageError: If the upload fails
        """
        logger.info(f"Uploading {local_path.name} to b2://{self.config.bucket}/{remote_key}")

        try:
            self.bucket.upload_local_file(
                local_file=str(local_path),
                file_name=remote_key,
            )
            logger.info(f"Upload completed: {remote_key}")
        except B2Error as e:
            logger.error(f"B2 upload failed: {e}")
            raise StorageError(f"Failed to upload to Backblaze B2: {e}")

    def list(self, prefix: str = "") -> list[StorageObject]:
        """List objects in the B2 bucket.

        Args:
            prefix: Filter objects by key prefix

        Returns:
            List of StorageObject instances

        Raises:
            StorageError: If listing fails
        """
        logger.debug(f"Listing objects with prefix '{prefix}'")

        try:
            objects = []

            for file_version, _ in self.bucket.ls(folder_to_list=prefix, latest_only=True):
                objects.append(
                    StorageObject(
                        key=file_version.file_name,
                        size=file_version.size,
                        last_modified=file_version.upload_timestamp,
                    )
                )

            logger.debug(f"Found {len(objects)} objects")
            return objects

        except B2Error as e:
            logger.error(f"B2 list failed: {e}")
            raise StorageError(f"Failed to list B2 objects: {e}")

    def delete(self, remote_key: str) -> None:
        """Delete an object from Backblaze B2.

        Args:
            remote_key: Key/path of the object to delete

        Raises:
            StorageError: If deletion fails
        """
        logger.info(f"Deleting b2://{self.config.bucket}/{remote_key}")

        try:
            file_versions = list(
                self.bucket.ls(folder_to_list=remote_key, latest_only=False)
            )

            for file_version, _ in file_versions:
                if file_version.file_name == remote_key:
                    self.api.delete_file_version(
                        file_version.id_, file_version.file_name
                    )

            logger.debug(f"Deleted: {remote_key}")
        except B2Error as e:
            logger.error(f"B2 delete failed: {e}")
            raise StorageError(f"Failed to delete B2 object: {e}")

    def delete_many(self, remote_keys: list[str]) -> None:
        """Delete multiple objects from Backblaze B2.

        Args:
            remote_keys: List of keys to delete

        Raises:
            StorageError: If deletion fails
        """
        if not remote_keys:
            return

        logger.info(f"Deleting {len(remote_keys)} objects from B2")

        for key in remote_keys:
            self.delete(key)

        logger.info(f"Deleted {len(remote_keys)} objects")
