"""Tests for PostgreSQL backup adapter."""

import subprocess
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from nestvault.backup.postgres import PostgresBackupAdapter
from nestvault.config import PostgresConfig
from nestvault.exceptions import BackupError


class TestPostgresBackupAdapter:
    """Tests for PostgresBackupAdapter."""

    @pytest.fixture
    def config(self):
        return PostgresConfig(
            host="localhost",
            port=5432,
            database="testdb",
            user="testuser",
            password="testpass",
        )

    @pytest.fixture
    def adapter(self, config):
        return PostgresBackupAdapter(config)

    def test_database_name(self, adapter):
        assert adapter.database_name == "testdb"

    def test_file_extension(self, adapter):
        assert adapter.file_extension == "sql.gz"

    def test_backup_success(self, adapter):
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(
                stdout=b"-- PostgreSQL dump\nCREATE TABLE test;",
                returncode=0,
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir)
                backup_file = adapter.backup(output_path)

                assert backup_file.exists()
                assert backup_file.suffix == ".gz"
                assert "testdb" in backup_file.name

    def test_backup_failure(self, adapter):
        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd=["pg_dump"],
                stderr=b"connection refused",
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir)

                with pytest.raises(BackupError) as exc_info:
                    adapter.backup(output_path)

                assert "connection refused" in str(exc_info.value)

    def test_backup_command_args(self, adapter):
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(stdout=b"", returncode=0)

            with tempfile.TemporaryDirectory() as temp_dir:
                adapter.backup(Path(temp_dir))

                call_args = mock_run.call_args
                cmd = call_args[0][0]

                assert "pg_dump" in cmd
                assert "-h" in cmd
                assert "localhost" in cmd
                assert "-d" in cmd
                assert "testdb" in cmd
