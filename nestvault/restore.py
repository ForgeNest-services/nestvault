"""Restore functionality for NestVault."""

from __future__ import annotations

import tempfile
from pathlib import Path

from nestvault.backup.base import BackupAdapter
from nestvault.exceptions import BackupError, StorageError
from nestvault.logging import get_logger
from nestvault.storage.base import StorageAdapter

logger = get_logger("restore")


def list_available_backups(
    storage_adapter: StorageAdapter,
    database_name: str | None = None,
) -> list[str]:
    """List available backups in storage.

    Args:
        storage_adapter: Storage adapter
        database_name: Optional filter by database name prefix

    Returns:
        List of backup keys sorted by date (newest first)
    """
    prefix = database_name or ""
    objects = storage_adapter.list(prefix=prefix)

    # Sort by last_modified descending (newest first)
    objects.sort(key=lambda x: x.last_modified, reverse=True)

    return [obj.key for obj in objects]


def restore_backup(
    storage_adapter: StorageAdapter,
    backup_adapter: BackupAdapter,
    backup_key: str,
) -> bool:
    """Restore a specific backup.

    Args:
        storage_adapter: Storage adapter to download from
        backup_adapter: Database backup adapter to restore with
        backup_key: Key of the backup to restore

    Returns:
        True if restore succeeded, False otherwise
    """
    logger.info(f"Starting restore of backup: {backup_key}")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            local_file = temp_path / backup_key

            # Download backup from storage
            logger.info(f"Downloading backup from storage...")
            storage_adapter.download(backup_key, local_file)
            logger.info(f"Downloaded: {local_file.name} ({local_file.stat().st_size} bytes)")

            # Restore to database
            logger.info(f"Restoring to database...")
            backup_adapter.restore(local_file)

        logger.info("Restore completed successfully")
        return True

    except StorageError as e:
        logger.error(f"Failed to download backup: {e}")
        return False
    except BackupError as e:
        logger.error(f"Failed to restore backup: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during restore: {e}")
        return False


def restore_latest_backup(
    storage_adapter: StorageAdapter,
    backup_adapter: BackupAdapter,
) -> bool:
    """Restore the most recent backup for the configured database.

    Args:
        storage_adapter: Storage adapter to download from
        backup_adapter: Database backup adapter to restore with

    Returns:
        True if restore succeeded, False otherwise
    """
    database_name = backup_adapter.database_name
    logger.info(f"Finding latest backup for database: {database_name}")

    backups = list_available_backups(storage_adapter, database_name)

    if not backups:
        logger.error(f"No backups found for database: {database_name}")
        return False

    latest = backups[0]
    logger.info(f"Found {len(backups)} backups, restoring latest: {latest}")

    return restore_backup(storage_adapter, backup_adapter, latest)
