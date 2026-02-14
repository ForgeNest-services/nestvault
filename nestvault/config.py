"""Environment variable parsing and validation for NestVault."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse, unquote

from croniter import croniter

from nestvault.exceptions import ConfigError


DatabaseType = Literal["postgres", "mongodb"]
StorageType = Literal["s3", "backblaze", "r2"]


@dataclass
class PostgresConfig:
    """PostgreSQL connection configuration."""

    host: str
    port: int
    database: str
    user: str
    password: str


@dataclass
class MongoDBConfig:
    """MongoDB connection configuration."""

    uri: str
    database: str


@dataclass
class S3Config:
    """S3/R2 storage configuration."""

    access_key: str
    secret_key: str
    bucket: str
    region: str
    endpoint: str | None = None


@dataclass
class BackblazeConfig:
    """Backblaze B2 storage configuration."""

    key_id: str
    application_key: str
    bucket: str
    region: str


@dataclass
class Config:
    """Main configuration container."""

    database_type: DatabaseType
    storage_type: StorageType
    backup_schedule: str
    retention_days: int
    log_level: str

    postgres: PostgresConfig | None = None
    mongodb: MongoDBConfig | None = None
    s3: S3Config | None = None
    backblaze: BackblazeConfig | None = None


def _get_required_env(name: str) -> str:
    """Get a required environment variable or raise ConfigError."""
    value = os.environ.get(name)
    if not value:
        raise ConfigError(f"Missing required environment variable: {name}")
    return value


def _get_optional_env(name: str, default: str | None = None) -> str | None:
    """Get an optional environment variable with a default."""
    return os.environ.get(name, default)


def _get_int_env(name: str, default: int | None = None) -> int:
    """Get an integer environment variable."""
    value = os.environ.get(name)
    if value is None:
        if default is not None:
            return default
        raise ConfigError(f"Missing required environment variable: {name}")
    try:
        return int(value)
    except ValueError:
        raise ConfigError(f"Environment variable {name} must be an integer, got: {value}")


def _validate_cron(expression: str) -> None:
    """Validate a cron expression."""
    try:
        croniter(expression)
    except (ValueError, KeyError) as e:
        raise ConfigError(f"Invalid cron expression '{expression}': {e}")


def _parse_database_url(url: str) -> PostgresConfig:
    """Parse a DATABASE_URL into PostgresConfig.

    Supports formats:
        postgresql://user:password@host:port/database
        postgres://user:password@host:port/database
    """
    parsed = urlparse(url)

    if parsed.scheme not in ("postgresql", "postgres"):
        raise ConfigError(f"Invalid DATABASE_URL scheme: {parsed.scheme}. Must be 'postgresql' or 'postgres'")

    if not parsed.hostname:
        raise ConfigError("DATABASE_URL missing hostname")
    if not parsed.username:
        raise ConfigError("DATABASE_URL missing username")
    if not parsed.password:
        raise ConfigError("DATABASE_URL missing password")
    if not parsed.path or parsed.path == "/":
        raise ConfigError("DATABASE_URL missing database name")

    database = parsed.path.lstrip("/")

    return PostgresConfig(
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=unquote(database),
        user=unquote(parsed.username),
        password=unquote(parsed.password),
    )


def _load_postgres_config() -> PostgresConfig:
    """Load PostgreSQL configuration from environment.

    Supports two modes:
        1. DATABASE_URL - single connection string (preferred)
        2. Separate PG_* variables - legacy/explicit mode
    """
    database_url = _get_optional_env("DATABASE_URL")

    if database_url:
        return _parse_database_url(database_url)

    return PostgresConfig(
        host=_get_required_env("PG_HOST"),
        port=_get_int_env("PG_PORT", 5432),
        database=_get_required_env("PG_DATABASE"),
        user=_get_required_env("PG_USER"),
        password=_get_required_env("PG_PASSWORD"),
    )


def _parse_mongodb_url(url: str) -> MongoDBConfig:
    """Parse a DATABASE_URL into MongoDBConfig.

    Supports format:
        mongodb://user:password@host:port/database?authSource=admin
    """
    parsed = urlparse(url)

    if parsed.scheme not in ("mongodb", "mongodb+srv"):
        raise ConfigError(f"Invalid DATABASE_URL scheme: {parsed.scheme}. Must be 'mongodb' or 'mongodb+srv'")

    if not parsed.path or parsed.path == "/":
        raise ConfigError("DATABASE_URL missing database name")

    database = parsed.path.lstrip("/").split("?")[0]

    return MongoDBConfig(
        uri=url,
        database=database,
    )


def _load_mongodb_config() -> MongoDBConfig:
    """Load MongoDB configuration from environment.

    Supports two modes:
        1. DATABASE_URL - single connection string (preferred)
        2. Separate MONGO_URI + MONGO_DATABASE - legacy/explicit mode
    """
    database_url = _get_optional_env("DATABASE_URL")

    if database_url:
        return _parse_mongodb_url(database_url)

    return MongoDBConfig(
        uri=_get_required_env("MONGO_URI"),
        database=_get_required_env("MONGO_DATABASE"),
    )


def _load_s3_config(include_endpoint: bool = False) -> S3Config:
    """Load S3 configuration from environment."""
    return S3Config(
        access_key=_get_required_env("S3_ACCESS_KEY"),
        secret_key=_get_required_env("S3_SECRET_KEY"),
        bucket=_get_required_env("S3_BUCKET"),
        region=_get_required_env("S3_REGION"),
        endpoint=_get_required_env("S3_ENDPOINT") if include_endpoint else _get_optional_env("S3_ENDPOINT"),
    )


def _load_backblaze_config() -> BackblazeConfig:
    """Load Backblaze B2 configuration from environment."""
    return BackblazeConfig(
        key_id=_get_required_env("B2_KEY_ID"),
        application_key=_get_required_env("B2_APPLICATION_KEY"),
        bucket=_get_required_env("B2_BUCKET"),
        region=_get_required_env("B2_REGION"),
    )


def load_config() -> Config:
    """Load and validate configuration from environment variables.

    Returns:
        Validated Config object

    Raises:
        ConfigError: If configuration is invalid or missing required values
    """
    database_type = _get_required_env("DATABASE_TYPE").lower()
    if database_type not in ("postgres", "mongodb"):
        raise ConfigError(f"Invalid DATABASE_TYPE: {database_type}. Must be 'postgres' or 'mongodb'")

    storage_type = _get_required_env("STORAGE_TYPE").lower()
    if storage_type not in ("s3", "backblaze", "r2"):
        raise ConfigError(f"Invalid STORAGE_TYPE: {storage_type}. Must be 's3', 'backblaze', or 'r2'")

    backup_schedule = _get_required_env("BACKUP_SCHEDULE")
    _validate_cron(backup_schedule)

    retention_days = _get_int_env("RETENTION_DAYS")
    if retention_days < 1:
        raise ConfigError(f"RETENTION_DAYS must be at least 1, got: {retention_days}")

    log_level = _get_optional_env("LOG_LEVEL", "INFO").upper()
    if log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        raise ConfigError(f"Invalid LOG_LEVEL: {log_level}")

    config = Config(
        database_type=database_type,  # type: ignore
        storage_type=storage_type,  # type: ignore
        backup_schedule=backup_schedule,
        retention_days=retention_days,
        log_level=log_level,
    )

    if database_type == "postgres":
        config.postgres = _load_postgres_config()
    elif database_type == "mongodb":
        config.mongodb = _load_mongodb_config()

    if storage_type == "s3":
        config.s3 = _load_s3_config()
    elif storage_type == "r2":
        config.s3 = _load_s3_config(include_endpoint=True)
    elif storage_type == "backblaze":
        config.backblaze = _load_backblaze_config()

    return config
