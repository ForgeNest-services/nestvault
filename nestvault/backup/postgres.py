"""PostgreSQL backup adapter using pg_dump."""

import gzip
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from nestvault.backup.base import BackupAdapter
from nestvault.config import PostgresConfig
from nestvault.exceptions import BackupError
from nestvault.logging import get_logger

logger = get_logger("backup.postgres")


class PostgresBackupAdapter(BackupAdapter):
    """Backup adapter for PostgreSQL databases using pg_dump."""

    def __init__(self, config: PostgresConfig):
        """Initialize the PostgreSQL backup adapter.

        Args:
            config: PostgreSQL connection configuration
        """
        self.config = config

    @property
    def database_name(self) -> str:
        """Return the name of the database being backed up."""
        return self.config.database

    @property
    def file_extension(self) -> str:
        """Return the file extension for backup files."""
        return "sql.gz"

    def backup(self, output_path: Path) -> Path:
        """Create a backup of the PostgreSQL database.

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

        logger.info(f"Starting PostgreSQL backup for database '{self.database_name}'")

        env = {
            "PGPASSWORD": self.config.password,
        }

        cmd = [
            "pg_dump",
            "-h", self.config.host,
            "-p", str(self.config.port),
            "-U", self.config.user,
            "-d", self.config.database,
            "--no-password",
        ]

        try:
            logger.debug(f"Executing pg_dump command")
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                check=True,
            )

            logger.debug(f"Compressing backup to {backup_file}")
            with gzip.open(backup_file, "wb") as f:
                f.write(result.stdout)

            file_size = backup_file.stat().st_size
            logger.info(f"Backup completed: {filename} ({file_size} bytes)")

            return backup_file

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"pg_dump failed: {error_msg}")
            raise BackupError(f"PostgreSQL backup failed: {error_msg}")
        except OSError as e:
            logger.error(f"Failed to write backup file: {e}")
            raise BackupError(f"Failed to write backup file: {e}")

    def restore(self, backup_file: Path) -> None:
        """Restore a PostgreSQL database from a backup file.

        Args:
            backup_file: Path to the backup file (.sql.gz)

        Raises:
            BackupError: If the restore operation fails
        """
        logger.info(f"Starting PostgreSQL restore for database '{self.database_name}'")
        logger.info(f"Restoring from: {backup_file}")

        env = {
            "PGPASSWORD": self.config.password,
        }

        cmd = [
            "psql",
            "-h", self.config.host,
            "-p", str(self.config.port),
            "-U", self.config.user,
            "-d", self.config.database,
            "--no-password",
        ]

        try:
            logger.debug("Decompressing and executing restore")
            with gzip.open(backup_file, "rb") as f:
                sql_content = f.read()

            result = subprocess.run(
                cmd,
                env=env,
                input=sql_content,
                capture_output=True,
                check=True,
            )

            logger.info(f"Restore completed successfully for database '{self.database_name}'")

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"psql restore failed: {error_msg}")
            raise BackupError(f"PostgreSQL restore failed: {error_msg}")
        except OSError as e:
            logger.error(f"Failed to read backup file: {e}")
            raise BackupError(f"Failed to read backup file: {e}")
