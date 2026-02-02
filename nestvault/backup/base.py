"""Abstract base class for backup adapters."""

from abc import ABC, abstractmethod
from pathlib import Path


class BackupAdapter(ABC):
    """Abstract base class for database backup adapters."""

    @abstractmethod
    def backup(self, output_path: Path) -> Path:
        """Create a backup of the database.

        Args:
            output_path: Directory to write the backup file to

        Returns:
            Path to the created backup file (compressed)

        Raises:
            BackupError: If the backup operation fails
        """
        pass

    @property
    @abstractmethod
    def database_name(self) -> str:
        """Return the name of the database being backed up."""
        pass

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Return the file extension for backup files (e.g., 'sql.gz', 'archive.gz')."""
        pass
