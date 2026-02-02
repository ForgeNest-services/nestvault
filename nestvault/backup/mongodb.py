"""MongoDB backup adapter using mongodump."""

import shutil
import subprocess
import tempfile
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
