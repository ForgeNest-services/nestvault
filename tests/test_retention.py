"""Tests for retention module."""

from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest

from nestvault.retention import get_expired_backups, cleanup_old_backups
from nestvault.storage.base import StorageObject


class TestGetExpiredBackups:
    """Tests for get_expired_backups function."""

    def test_no_expired_backups(self):
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        objects = [
            StorageObject(
                key="db_20240114_120000.sql.gz",
                size=1000,
                last_modified=datetime(2024, 1, 14, 12, 0, 0, tzinfo=timezone.utc),
            ),
            StorageObject(
                key="db_20240115_060000.sql.gz",
                size=1000,
                last_modified=datetime(2024, 1, 15, 6, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        expired = get_expired_backups(objects, retention_days=7, now=now)
        assert len(expired) == 0

    def test_some_expired_backups(self):
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        objects = [
            StorageObject(
                key="db_20240101_120000.sql.gz",
                size=1000,
                last_modified=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            StorageObject(
                key="db_20240107_120000.sql.gz",
                size=1000,
                last_modified=datetime(2024, 1, 7, 12, 0, 0, tzinfo=timezone.utc),
            ),
            StorageObject(
                key="db_20240114_120000.sql.gz",
                size=1000,
                last_modified=datetime(2024, 1, 14, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        expired = get_expired_backups(objects, retention_days=7, now=now)
        assert len(expired) == 2
        assert expired[0].key == "db_20240101_120000.sql.gz"
        assert expired[1].key == "db_20240107_120000.sql.gz"

    def test_all_expired_backups(self):
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        objects = [
            StorageObject(
                key="db_20240101_120000.sql.gz",
                size=1000,
                last_modified=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        expired = get_expired_backups(objects, retention_days=7, now=now)
        assert len(expired) == 1

    def test_empty_list(self):
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        expired = get_expired_backups([], retention_days=7, now=now)
        assert len(expired) == 0

    def test_handles_naive_datetime(self):
        """Test that naive datetimes are handled correctly."""
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        objects = [
            StorageObject(
                key="db_20240101_120000.sql.gz",
                size=1000,
                last_modified=datetime(2024, 1, 1, 12, 0, 0),  # Naive datetime
            ),
        ]

        expired = get_expired_backups(objects, retention_days=7, now=now)
        assert len(expired) == 1

    def test_boundary_condition(self):
        """Test backup exactly at retention cutoff."""
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        cutoff = now - timedelta(days=7)

        objects = [
            StorageObject(
                key="db_at_cutoff.sql.gz",
                size=1000,
                last_modified=cutoff,
            ),
            StorageObject(
                key="db_before_cutoff.sql.gz",
                size=1000,
                last_modified=cutoff - timedelta(seconds=1),
            ),
        ]

        expired = get_expired_backups(objects, retention_days=7, now=now)
        assert len(expired) == 1
        assert expired[0].key == "db_before_cutoff.sql.gz"


class TestCleanupOldBackups:
    """Tests for cleanup_old_backups function."""

    def test_deletes_expired_backups(self):
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        objects = [
            StorageObject(
                key="db_20240101_120000.sql.gz",
                size=1000,
                last_modified=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            StorageObject(
                key="db_20240114_120000.sql.gz",
                size=1000,
                last_modified=datetime(2024, 1, 14, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        mock_storage = mock.Mock()
        mock_storage.list.return_value = objects

        with mock.patch("nestvault.retention.datetime") as mock_datetime:
            mock_datetime.now.return_value = now

            deleted_count = cleanup_old_backups(
                mock_storage, retention_days=7, prefix="db"
            )

        assert deleted_count == 1
        mock_storage.delete_many.assert_called_once_with(["db_20240101_120000.sql.gz"])

    def test_no_deletions_when_all_fresh(self):
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        objects = [
            StorageObject(
                key="db_20240114_120000.sql.gz",
                size=1000,
                last_modified=datetime(2024, 1, 14, 12, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        mock_storage = mock.Mock()
        mock_storage.list.return_value = objects

        with mock.patch("nestvault.retention.datetime") as mock_datetime:
            mock_datetime.now.return_value = now

            deleted_count = cleanup_old_backups(
                mock_storage, retention_days=7, prefix="db"
            )

        assert deleted_count == 0
        mock_storage.delete_many.assert_not_called()
