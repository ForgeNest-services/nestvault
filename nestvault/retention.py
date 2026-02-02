"""Backup retention and cleanup logic."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from nestvault.exceptions import RetentionError
from nestvault.logging import get_logger
from nestvault.storage.base import StorageAdapter, StorageObject

logger = get_logger("retention")


def get_expired_backups(
    objects: list[StorageObject],
    retention_days: int,
    now: datetime | None = None,
) -> list[StorageObject]:
    """Identify backups that have exceeded the retention period.

    Args:
        objects: List of storage objects to check
        retention_days: Number of days to retain backups
        now: Current time (defaults to UTC now, useful for testing)

    Returns:
        List of StorageObject instances that should be deleted
    """
    if now is None:
        now = datetime.now(timezone.utc)

    cutoff = now - timedelta(days=retention_days)
    expired = []

    for obj in objects:
        last_modified = obj.last_modified
        if last_modified.tzinfo is None:
            last_modified = last_modified.replace(tzinfo=timezone.utc)

        if last_modified < cutoff:
            expired.append(obj)

    return expired


def cleanup_old_backups(
    storage: StorageAdapter,
    retention_days: int,
    prefix: str = "",
) -> int:
    """Delete backups older than the retention period.

    Args:
        storage: Storage adapter to use
        retention_days: Number of days to retain backups
        prefix: Optional prefix to filter backups

    Returns:
        Number of backups deleted

    Raises:
        RetentionError: If cleanup fails
    """
    logger.info(f"Starting retention cleanup (retention_days={retention_days})")

    try:
        objects = storage.list(prefix=prefix)
        logger.debug(f"Found {len(objects)} total objects")

        expired = get_expired_backups(objects, retention_days)

        if not expired:
            logger.info("No expired backups to delete")
            return 0

        logger.info(f"Found {len(expired)} expired backups to delete")

        keys_to_delete = [obj.key for obj in expired]
        storage.delete_many(keys_to_delete)

        logger.info(f"Retention cleanup completed: deleted {len(expired)} backups")
        return len(expired)

    except Exception as e:
        logger.error(f"Retention cleanup failed: {e}")
        raise RetentionError(f"Failed to cleanup old backups: {e}")
