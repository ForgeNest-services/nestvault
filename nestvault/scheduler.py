"""Cron-based backup scheduler."""

from __future__ import annotations

import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from croniter import croniter

from nestvault.backup.base import BackupAdapter
from nestvault.config import Config
from nestvault.exceptions import BackupError, StorageError
from nestvault.logging import get_logger
from nestvault.retention import cleanup_old_backups
from nestvault.storage.base import StorageAdapter

logger = get_logger("scheduler")


def get_next_run_time(cron_expression: str, base_time: datetime | None = None) -> datetime:
    """Calculate the next run time based on a cron expression.

    Args:
        cron_expression: Cron expression string
        base_time: Base time for calculation (defaults to UTC now)

    Returns:
        Next scheduled run time as datetime
    """
    if base_time is None:
        base_time = datetime.now(timezone.utc)

    cron = croniter(cron_expression, base_time)
    return cron.get_next(datetime)


def run_backup_job(
    backup_adapter: BackupAdapter,
    storage_adapter: StorageAdapter,
    retention_days: int,
) -> bool:
    """Execute a single backup job.

    Args:
        backup_adapter: Database backup adapter
        storage_adapter: Storage adapter
        retention_days: Number of days to retain backups

    Returns:
        True if backup succeeded, False otherwise
    """
    logger.info("Starting backup job")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            backup_file = backup_adapter.backup(temp_path)
            logger.info(f"Backup created: {backup_file.name}")

            remote_key = backup_file.name
            storage_adapter.upload(backup_file, remote_key)
            logger.info(f"Backup uploaded: {remote_key}")

        deleted_count = cleanup_old_backups(
            storage_adapter,
            retention_days,
            prefix=backup_adapter.database_name,
        )

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old backups")

        logger.info("Backup job completed successfully")
        return True

    except BackupError as e:
        logger.error(f"Backup failed: {e}")
        return False
    except StorageError as e:
        logger.error(f"Storage operation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during backup: {e}")
        return False


def run_scheduler(
    config: Config,
    backup_adapter: BackupAdapter,
    storage_adapter: StorageAdapter,
    run_immediately: bool = True,
) -> None:
    """Run the backup scheduler loop.

    Args:
        config: Application configuration
        backup_adapter: Database backup adapter
        storage_adapter: Storage adapter
        run_immediately: If True, run a backup immediately on start
    """
    logger.info(f"Starting scheduler with schedule: {config.backup_schedule}")
    logger.info(f"Retention policy: {config.retention_days} days")

    if run_immediately:
        logger.info("Running initial backup")
        run_backup_job(backup_adapter, storage_adapter, config.retention_days)

    while True:
        next_run = get_next_run_time(config.backup_schedule)
        logger.info(f"Next backup scheduled for: {next_run.isoformat()}")

        now = datetime.now(timezone.utc)
        wait_seconds = (next_run - now).total_seconds()

        if wait_seconds > 0:
            logger.debug(f"Sleeping for {wait_seconds:.0f} seconds")
            time.sleep(wait_seconds)

        run_backup_job(backup_adapter, storage_adapter, config.retention_days)
