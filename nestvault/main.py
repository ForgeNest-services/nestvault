"""Main entry point for NestVault."""

import sys

from nestvault.backup.base import BackupAdapter
from nestvault.backup.mongodb import MongoDBBackupAdapter
from nestvault.backup.postgres import PostgresBackupAdapter
from nestvault.cli import parse_args
from nestvault.config import Config, load_config
from nestvault.exceptions import ConfigError, NestVaultError
from nestvault.logging import get_logger, setup_logging
from nestvault.restore import list_available_backups, restore_backup, restore_latest_backup
from nestvault.scheduler import run_scheduler
from nestvault.storage.backblaze import BackblazeStorageAdapter
from nestvault.storage.base import StorageAdapter
from nestvault.storage.r2 import R2StorageAdapter
from nestvault.storage.s3 import S3StorageAdapter


def create_backup_adapter(config: Config) -> BackupAdapter:
    """Create the appropriate backup adapter based on configuration.

    Args:
        config: Application configuration

    Returns:
        Configured backup adapter
    """
    if config.database_type == "postgres":
        if not config.postgres:
            raise ConfigError("PostgreSQL configuration missing")
        return PostgresBackupAdapter(config.postgres)
    elif config.database_type == "mongodb":
        if not config.mongodb:
            raise ConfigError("MongoDB configuration missing")
        return MongoDBBackupAdapter(config.mongodb)
    else:
        raise ConfigError(f"Unknown database type: {config.database_type}")


def create_storage_adapter(config: Config) -> StorageAdapter:
    """Create the appropriate storage adapter based on configuration.

    Args:
        config: Application configuration

    Returns:
        Configured storage adapter
    """
    if config.storage_type == "s3":
        if not config.s3:
            raise ConfigError("S3 configuration missing")
        return S3StorageAdapter(config.s3)
    elif config.storage_type == "r2":
        if not config.s3:
            raise ConfigError("R2 configuration missing")
        return R2StorageAdapter(config.s3)
    elif config.storage_type == "backblaze":
        if not config.backblaze:
            raise ConfigError("Backblaze configuration missing")
        return BackblazeStorageAdapter(config.backblaze)
    else:
        raise ConfigError(f"Unknown storage type: {config.storage_type}")


def run_restore(args, config: Config, logger) -> int:
    """Run restore operation.

    Args:
        args: Parsed command line arguments
        config: Application configuration
        logger: Logger instance

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    backup_adapter = create_backup_adapter(config)
    storage_adapter = create_storage_adapter(config)

    # List backups only
    if args.list:
        logger.info("Listing available backups...")
        backups = list_available_backups(storage_adapter, backup_adapter.database_name)

        if not backups:
            logger.info(f"No backups found for database: {backup_adapter.database_name}")
            return 0

        logger.info(f"Found {len(backups)} backups:")
        for backup in backups:
            print(f"  - {backup}")
        return 0

    # Restore specific backup
    if args.backup:
        logger.info(f"Restoring specific backup: {args.backup}")
        success = restore_backup(storage_adapter, backup_adapter, args.backup)
    else:
        # Restore latest backup
        logger.info("Restoring latest backup...")
        success = restore_latest_backup(storage_adapter, backup_adapter)

    return 0 if success else 1


def main() -> int:
    """Main entry point for NestVault.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    args = parse_args()

    try:
        config = load_config()
        setup_logging(config.log_level)

        logger = get_logger("main")
        logger.info("NestVault starting")
        logger.info(f"Database type: {config.database_type}")
        logger.info(f"Storage type: {config.storage_type}")

        # Handle restore command
        if args.command == "restore":
            return run_restore(args, config, logger)

        # Default: run backup scheduler
        backup_adapter = create_backup_adapter(config)
        storage_adapter = create_storage_adapter(config)

        run_scheduler(config, backup_adapter, storage_adapter)

        return 0

    except ConfigError as e:
        setup_logging("ERROR")
        logger = get_logger("main")
        logger.error(f"Configuration error: {e}")
        return 1

    except NestVaultError as e:
        logger = get_logger("main")
        logger.error(f"NestVault error: {e}")
        return 1

    except KeyboardInterrupt:
        logger = get_logger("main")
        logger.info("Shutting down")
        return 0

    except Exception as e:
        setup_logging("ERROR")
        logger = get_logger("main")
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
