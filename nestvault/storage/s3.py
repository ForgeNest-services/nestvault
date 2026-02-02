"""S3 storage adapter using boto3."""

from __future__ import annotations

from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from nestvault.config import S3Config
from nestvault.exceptions import StorageError
from nestvault.logging import get_logger
from nestvault.storage.base import StorageAdapter, StorageObject

logger = get_logger("storage.s3")


class S3StorageAdapter(StorageAdapter):
    """Storage adapter for Amazon S3 and S3-compatible services."""

    def __init__(self, config: S3Config):
        """Initialize the S3 storage adapter.

        Args:
            config: S3 configuration
        """
        self.config = config
        self.bucket = config.bucket

        client_kwargs = {
            "aws_access_key_id": config.access_key,
            "aws_secret_access_key": config.secret_key,
            "region_name": config.region,
        }

        if config.endpoint:
            client_kwargs["endpoint_url"] = config.endpoint

        self.client = boto3.client("s3", **client_kwargs)
        logger.debug(f"Initialized S3 client for bucket '{self.bucket}'")

    def upload(self, local_path: Path, remote_key: str) -> None:
        """Upload a file to S3.

        Args:
            local_path: Path to the local file
            remote_key: Key/path in the S3 bucket

        Raises:
            StorageError: If the upload fails
        """
        logger.info(f"Uploading {local_path.name} to s3://{self.bucket}/{remote_key}")

        try:
            self.client.upload_file(str(local_path), self.bucket, remote_key)
            logger.info(f"Upload completed: {remote_key}")
        except (BotoCoreError, ClientError) as e:
            logger.error(f"S3 upload failed: {e}")
            raise StorageError(f"Failed to upload to S3: {e}")

    def list(self, prefix: str = "") -> list[StorageObject]:
        """List objects in the S3 bucket.

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
            paginator = self.client.get_paginator("list_objects_v2")

            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    objects.append(
                        StorageObject(
                            key=obj["Key"],
                            size=obj["Size"],
                            last_modified=obj["LastModified"],
                        )
                    )

            logger.debug(f"Found {len(objects)} objects")
            return objects

        except (BotoCoreError, ClientError) as e:
            logger.error(f"S3 list failed: {e}")
            raise StorageError(f"Failed to list S3 objects: {e}")

    def delete(self, remote_key: str) -> None:
        """Delete an object from S3.

        Args:
            remote_key: Key/path of the object to delete

        Raises:
            StorageError: If deletion fails
        """
        logger.info(f"Deleting s3://{self.bucket}/{remote_key}")

        try:
            self.client.delete_object(Bucket=self.bucket, Key=remote_key)
            logger.debug(f"Deleted: {remote_key}")
        except (BotoCoreError, ClientError) as e:
            logger.error(f"S3 delete failed: {e}")
            raise StorageError(f"Failed to delete S3 object: {e}")

    def delete_many(self, remote_keys: list[str]) -> None:
        """Delete multiple objects from S3.

        Args:
            remote_keys: List of keys to delete

        Raises:
            StorageError: If deletion fails
        """
        if not remote_keys:
            return

        logger.info(f"Deleting {len(remote_keys)} objects from S3")

        try:
            delete_objects = [{"Key": key} for key in remote_keys]

            for i in range(0, len(delete_objects), 1000):
                batch = delete_objects[i : i + 1000]
                self.client.delete_objects(
                    Bucket=self.bucket, Delete={"Objects": batch}
                )

            logger.info(f"Deleted {len(remote_keys)} objects")

        except (BotoCoreError, ClientError) as e:
            logger.error(f"S3 bulk delete failed: {e}")
            raise StorageError(f"Failed to delete S3 objects: {e}")
