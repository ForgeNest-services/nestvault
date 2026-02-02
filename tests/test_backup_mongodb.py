"""Tests for MongoDB backup adapter."""

import subprocess
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from nestvault.backup.mongodb import MongoDBBackupAdapter
from nestvault.config import MongoDBConfig
from nestvault.exceptions import BackupError


class TestMongoDBBackupAdapter:
    """Tests for MongoDBBackupAdapter."""

    @pytest.fixture
    def config(self):
        return MongoDBConfig(
            uri="mongodb://localhost:27017",
            database="testdb",
        )

    @pytest.fixture
    def adapter(self, config):
        return MongoDBBackupAdapter(config)

    def test_database_name(self, adapter):
        assert adapter.database_name == "testdb"

    def test_file_extension(self, adapter):
        assert adapter.file_extension == "archive.gz"

    def test_backup_success(self, adapter):
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(
                stdout=b"mongodb archive data",
                returncode=0,
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir)
                backup_file = adapter.backup(output_path)

                assert backup_file.exists()
                assert "testdb" in backup_file.name
                assert backup_file.name.endswith(".archive.gz")

    def test_backup_failure(self, adapter):
        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd=["mongodump"],
                stderr=b"authentication failed",
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir)

                with pytest.raises(BackupError) as exc_info:
                    adapter.backup(output_path)

                assert "authentication failed" in str(exc_info.value)

    def test_backup_command_args(self, adapter):
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(stdout=b"", returncode=0)

            with tempfile.TemporaryDirectory() as temp_dir:
                adapter.backup(Path(temp_dir))

                call_args = mock_run.call_args
                cmd = call_args[0][0]

                assert "mongodump" in cmd
                assert "--uri" in cmd
                assert "--db" in cmd
                assert "testdb" in cmd
                assert "--archive" in cmd
                assert "--gzip" in cmd
