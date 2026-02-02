"""Tests for configuration module."""

import os
from unittest import mock

import pytest

from nestvault.config import (
    Config,
    _get_required_env,
    _get_int_env,
    _validate_cron,
    load_config,
)
from nestvault.exceptions import ConfigError


class TestGetRequiredEnv:
    """Tests for _get_required_env function."""

    def test_returns_value_when_present(self):
        with mock.patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            assert _get_required_env("TEST_VAR") == "test_value"

    def test_raises_when_missing(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigError) as exc_info:
                _get_required_env("MISSING_VAR")
            assert "MISSING_VAR" in str(exc_info.value)

    def test_raises_when_empty(self):
        with mock.patch.dict(os.environ, {"EMPTY_VAR": ""}):
            with pytest.raises(ConfigError):
                _get_required_env("EMPTY_VAR")


class TestGetIntEnv:
    """Tests for _get_int_env function."""

    def test_returns_int_when_valid(self):
        with mock.patch.dict(os.environ, {"INT_VAR": "42"}):
            assert _get_int_env("INT_VAR") == 42

    def test_returns_default_when_missing(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            assert _get_int_env("MISSING_INT", default=10) == 10

    def test_raises_when_invalid(self):
        with mock.patch.dict(os.environ, {"INVALID_INT": "not_a_number"}):
            with pytest.raises(ConfigError) as exc_info:
                _get_int_env("INVALID_INT")
            assert "must be an integer" in str(exc_info.value)


class TestValidateCron:
    """Tests for _validate_cron function."""

    def test_valid_cron_expressions(self):
        valid_expressions = [
            "* * * * *",
            "0 * * * *",
            "0 0 * * *",
            "0 0 1 * *",
            "0 0 * * 0",
            "*/5 * * * *",
            "0 0,12 * * *",
        ]
        for expr in valid_expressions:
            _validate_cron(expr)

    def test_invalid_cron_expression(self):
        with pytest.raises(ConfigError):
            _validate_cron("invalid cron")


class TestLoadConfig:
    """Tests for load_config function."""

    @pytest.fixture
    def postgres_s3_env(self):
        """Environment variables for PostgreSQL + S3 configuration."""
        return {
            "DATABASE_TYPE": "postgres",
            "STORAGE_TYPE": "s3",
            "BACKUP_SCHEDULE": "0 * * * *",
            "RETENTION_DAYS": "7",
            "PG_HOST": "localhost",
            "PG_PORT": "5432",
            "PG_DATABASE": "testdb",
            "PG_USER": "testuser",
            "PG_PASSWORD": "testpass",
            "S3_ACCESS_KEY": "access_key",
            "S3_SECRET_KEY": "secret_key",
            "S3_BUCKET": "backups",
            "S3_REGION": "us-east-1",
        }

    @pytest.fixture
    def mongodb_backblaze_env(self):
        """Environment variables for MongoDB + Backblaze configuration."""
        return {
            "DATABASE_TYPE": "mongodb",
            "STORAGE_TYPE": "backblaze",
            "BACKUP_SCHEDULE": "0 0 * * *",
            "RETENTION_DAYS": "30",
            "MONGO_URI": "mongodb://localhost:27017",
            "MONGO_DATABASE": "testdb",
            "B2_KEY_ID": "key_id",
            "B2_APPLICATION_KEY": "app_key",
            "B2_BUCKET": "backups",
            "B2_REGION": "us-west-000",
        }

    def test_loads_postgres_s3_config(self, postgres_s3_env):
        with mock.patch.dict(os.environ, postgres_s3_env, clear=True):
            config = load_config()

            assert config.database_type == "postgres"
            assert config.storage_type == "s3"
            assert config.backup_schedule == "0 * * * *"
            assert config.retention_days == 7

            assert config.postgres is not None
            assert config.postgres.host == "localhost"
            assert config.postgres.database == "testdb"

            assert config.s3 is not None
            assert config.s3.bucket == "backups"

    def test_loads_mongodb_backblaze_config(self, mongodb_backblaze_env):
        with mock.patch.dict(os.environ, mongodb_backblaze_env, clear=True):
            config = load_config()

            assert config.database_type == "mongodb"
            assert config.storage_type == "backblaze"

            assert config.mongodb is not None
            assert config.mongodb.database == "testdb"

            assert config.backblaze is not None
            assert config.backblaze.bucket == "backups"

    def test_invalid_database_type(self, postgres_s3_env):
        postgres_s3_env["DATABASE_TYPE"] = "mysql"
        with mock.patch.dict(os.environ, postgres_s3_env, clear=True):
            with pytest.raises(ConfigError) as exc_info:
                load_config()
            assert "DATABASE_TYPE" in str(exc_info.value)

    def test_invalid_storage_type(self, postgres_s3_env):
        postgres_s3_env["STORAGE_TYPE"] = "azure"
        with mock.patch.dict(os.environ, postgres_s3_env, clear=True):
            with pytest.raises(ConfigError) as exc_info:
                load_config()
            assert "STORAGE_TYPE" in str(exc_info.value)

    def test_invalid_retention_days(self, postgres_s3_env):
        postgres_s3_env["RETENTION_DAYS"] = "0"
        with mock.patch.dict(os.environ, postgres_s3_env, clear=True):
            with pytest.raises(ConfigError) as exc_info:
                load_config()
            assert "RETENTION_DAYS" in str(exc_info.value)

    def test_r2_requires_endpoint(self, postgres_s3_env):
        postgres_s3_env["STORAGE_TYPE"] = "r2"
        with mock.patch.dict(os.environ, postgres_s3_env, clear=True):
            with pytest.raises(ConfigError):
                load_config()

    def test_r2_with_endpoint(self, postgres_s3_env):
        postgres_s3_env["STORAGE_TYPE"] = "r2"
        postgres_s3_env["S3_ENDPOINT"] = "https://account.r2.cloudflarestorage.com"
        with mock.patch.dict(os.environ, postgres_s3_env, clear=True):
            config = load_config()
            assert config.storage_type == "r2"
            assert config.s3.endpoint == "https://account.r2.cloudflarestorage.com"
