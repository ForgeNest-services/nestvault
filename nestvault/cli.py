"""Command line interface for NestVault."""

from __future__ import annotations

import argparse


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="NestVault - Container-native backup utility for PostgreSQL and MongoDB"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Backup command (default behavior)
    subparsers.add_parser("backup", help="Run backup scheduler (default)")

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument(
        "--backup",
        type=str,
        help="Specific backup file to restore (e.g., mydb_20240115_120000.sql.gz). "
             "If not specified, restores the latest backup.",
    )
    restore_parser.add_argument(
        "--list",
        action="store_true",
        help="List available backups without restoring",
    )

    return parser.parse_args()
