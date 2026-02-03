"""MongoDB backup adapter using mongodump."""

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from nestvault.backup.base import BackupAdapter
from nestvault.config import MongoDBConfig
from nestvault.exceptions import BackupError
from nestvault.logging import get_logger

logger = get_logger("backup.mongodb")


class MongoDBBackupAdapter(BackupAdapter):
    """Backup adapter for MongoDB databases using mongodump."""

    def __init__(self, config: MongoDBConfig):
        """Initialize the MongoDB backup adapter.

        Args:
            config: MongoDB connection configuration
        """
        self.config = config

    @property
    def database_name(self) -> str:
        """Return the name of the database being backed up."""
        return self.config.database

    @property
    def file_extension(self) -> str:
        """Return the file extension for backup files."""
        return "archive.gz"

    def backup(self, output_path: Path) -> Path:
        """Create a backup of the MongoDB database.

        Args:
            output_path: Directory to write the backup file to

        Returns:
            Path to the created backup file (compressed)

        Raises:
            BackupError: If the backup operation fails
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{self.database_name}_{timestamp}.{self.file_extension}"
        backup_file = output_path / filename

        logger.info(f"Starting MongoDB backup for database '{self.database_name}'")

        cmd = [
            "mongodump",
            "--uri", self.config.uri,
            "--db", self.config.database,
            "--archive",
            "--gzip",
        ]

        try:
            logger.debug("Executing mongodump command")
            result = subprocess.run(
                cmd,
                capture_output=True,
                check=True,
            )

            logger.debug(f"Writing backup to {backup_file}")
            with open(backup_file, "wb") as f:
                f.write(result.stdout)

            file_size = backup_file.stat().st_size
            logger.info(f"Backup completed: {filename} ({file_size} bytes)")

            return backup_file

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"mongodump failed: {error_msg}")
            raise BackupError(f"MongoDB backup failed: {error_msg}")
        except OSError as e:
            logger.error(f"Failed to write backup file: {e}")
            raise BackupError(f"Failed to write backup file: {e}")

    def restore(self, backup_file: Path) -> None:
        """Restore a MongoDB database from a backup file.

        Args:
            backup_file: Path to the backup file (.archive.gz)

        Raises:
            BackupError: If the restore operation fails
        """
        logger.info(f"Starting MongoDB restore for database '{self.database_name}'")
        logger.info(f"Restoring from: {backup_file}")

        cmd = [
            "mongorestore",
            "--uri", self.config.uri,
            "--db", self.config.database,
            "--archive=" + str(backup_file),
            "--gzip",
            "--drop",  # Drop existing collections before restoring
        ]

        try:
            logger.debug("Executing mongorestore command")
            result = subprocess.run(
                cmd,
                capture_output=True,
                check=True,
            )

            logger.info(f"Restore completed successfully for database '{self.database_name}'")

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"mongorestore failed: {error_msg}")
            raise BackupError(f"MongoDB restore failed: {error_msg}")
