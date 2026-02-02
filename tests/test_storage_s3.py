"""Tests for S3 storage adapter."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import pytest

from nestvault.config import S3Config
from nestvault.exceptions import StorageError
from nestvault.storage.s3 import S3StorageAdapter


class TestS3StorageAdapter:
    """Tests for S3StorageAdapter."""

    @pytest.fixture
    def config(self):
        return S3Config(
            access_key="test_access_key",
            secret_key="test_secret_key",
            bucket="test-bucket",
            region="us-east-1",
        )

    @pytest.fixture
    def mock_boto_client(self):
        with mock.patch("boto3.client") as mock_client:
            yield mock_client.return_value

    def test_upload_success(self, config, mock_boto_client):
        adapter = S3StorageAdapter(config)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test data")
            temp_path = Path(f.name)

        try:
            adapter.upload(temp_path, "backups/test.sql.gz")
            mock_boto_client.upload_file.assert_called_once()
        finally:
            temp_path.unlink()

    def test_upload_failure(self, config, mock_boto_client):
        from botocore.exceptions import ClientError

        mock_boto_client.upload_file.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
            "PutObject",
        )

        adapter = S3StorageAdapter(config)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test data")
            temp_path = Path(f.name)

        try:
            with pytest.raises(StorageError):
                adapter.upload(temp_path, "backups/test.sql.gz")
        finally:
            temp_path.unlink()

    def test_list_objects(self, config, mock_boto_client):
        mock_paginator = mock.Mock()
        mock_boto_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "Contents": [
                    {
                        "Key": "backups/db_20240115_120000.sql.gz",
                        "Size": 1024,
                        "LastModified": datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
                    },
                    {
                        "Key": "backups/db_20240114_120000.sql.gz",
                        "Size": 2048,
                        "LastModified": datetime(2024, 1, 14, 12, 0, 0, tzinfo=timezone.utc),
                    },
                ]
            }
        ]

        adapter = S3StorageAdapter(config)
        objects = adapter.list(prefix="backups/")

        assert len(objects) == 2
        assert objects[0].key == "backups/db_20240115_120000.sql.gz"
        assert objects[0].size == 1024

    def test_delete_object(self, config, mock_boto_client):
        adapter = S3StorageAdapter(config)
        adapter.delete("backups/test.sql.gz")

        mock_boto_client.delete_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="backups/test.sql.gz",
        )

    def test_delete_many_objects(self, config, mock_boto_client):
        adapter = S3StorageAdapter(config)
        keys = ["backups/file1.sql.gz", "backups/file2.sql.gz"]
        adapter.delete_many(keys)

        mock_boto_client.delete_objects.assert_called_once()
        call_args = mock_boto_client.delete_objects.call_args
        assert call_args[1]["Bucket"] == "test-bucket"
        assert len(call_args[1]["Delete"]["Objects"]) == 2

    def test_delete_many_empty_list(self, config, mock_boto_client):
        adapter = S3StorageAdapter(config)
        adapter.delete_many([])

        mock_boto_client.delete_objects.assert_not_called()

    def test_custom_endpoint(self):
        config = S3Config(
            access_key="test",
            secret_key="test",
            bucket="test",
            region="auto",
            endpoint="https://custom.endpoint.com",
        )

        with mock.patch("boto3.client") as mock_client:
            S3StorageAdapter(config)

            call_kwargs = mock_client.call_args[1]
            assert call_kwargs["endpoint_url"] == "https://custom.endpoint.com"
