"""Custom exceptions for NestVault."""


class NestVaultError(Exception):
    """Base exception for all NestVault errors."""

    pass


class ConfigError(NestVaultError):
    """Raised when configuration is invalid or missing."""

    pass


class BackupError(NestVaultError):
    """Raised when a backup operation fails."""

    pass


class StorageError(NestVaultError):
    """Raised when a storage operation fails."""

    pass


class RetentionError(NestVaultError):
    """Raised when retention cleanup fails."""

    pass
