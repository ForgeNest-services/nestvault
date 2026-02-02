"""Tests for scheduler module."""

from datetime import datetime, timezone
from unittest import mock

import pytest

from nestvault.scheduler import get_next_run_time, run_backup_job


class TestGetNextRunTime:
    """Tests for get_next_run_time function."""

    def test_hourly_schedule(self):
        base_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        next_run = get_next_run_time("0 * * * *", base_time)

        assert next_run.hour == 11
        assert next_run.minute == 0

    def test_daily_schedule(self):
        base_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        next_run = get_next_run_time("0 0 * * *", base_time)

        assert next_run.day == 16
        assert next_run.hour == 0
        assert next_run.minute == 0

    def test_every_5_minutes(self):
        base_time = datetime(2024, 1, 15, 10, 32, 0, tzinfo=timezone.utc)
        next_run = get_next_run_time("*/5 * * * *", base_time)

        assert next_run.minute == 35

    def test_specific_time(self):
        base_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        next_run = get_next_run_time("30 14 * * *", base_time)

        assert next_run.day == 15
        assert next_run.hour == 14
        assert next_run.minute == 30


class TestRunBackupJob:
    """Tests for run_backup_job function."""

    def test_successful_backup(self):
        mock_backup = mock.Mock()
        mock_backup.backup.return_value = mock.Mock(name="test_backup.sql.gz")
        mock_backup.database_name = "testdb"

        mock_storage = mock.Mock()
        mock_storage.list.return_value = []

        result = run_backup_job(mock_backup, mock_storage, retention_days=7)

        assert result is True
        mock_backup.backup.assert_called_once()
        mock_storage.upload.assert_called_once()

    def test_backup_failure(self):
        from nestvault.exceptions import BackupError

        mock_backup = mock.Mock()
        mock_backup.backup.side_effect = BackupError("pg_dump failed")

        mock_storage = mock.Mock()

        result = run_backup_job(mock_backup, mock_storage, retention_days=7)

        assert result is False
        mock_storage.upload.assert_not_called()

    def test_storage_failure(self):
        from nestvault.exceptions import StorageError

        mock_backup = mock.Mock()
        mock_backup.backup.return_value = mock.Mock(name="test_backup.sql.gz")

        mock_storage = mock.Mock()
        mock_storage.upload.side_effect = StorageError("S3 upload failed")

        result = run_backup_job(mock_backup, mock_storage, retention_days=7)

        assert result is False
