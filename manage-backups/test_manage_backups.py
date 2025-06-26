#!/usr/bin/env python3

"""Unit tests for manage_backups.py."""

import datetime
import logging
import pathlib
import subprocess
import unittest
from unittest.mock import MagicMock, patch

import manage_backups


class TestBackupFile(unittest.TestCase):
    """Tests for the BackupFile class."""

    def setUp(self):
        """Set up a mock path for tests."""
        self.mock_path = MagicMock(spec=pathlib.Path)
        self.backup_file = manage_backups.BackupFile(self.mock_path)

    def test_get_mtime(self):
        """Test that get_mtime returns the correct datetime object."""
        mock_stat_result = MagicMock()
        mock_stat_result.st_mtime = 1672531200  # 2023-01-01 00:00:00 UTC
        self.mock_path.stat.return_value = mock_stat_result

        expected_dt = datetime.datetime.fromtimestamp(1672531200)
        self.assertEqual(self.backup_file.get_mtime(), expected_dt)

    def test_is_older_than_dt(self):
        """Test that is_older_than_dt correctly compares times."""
        with patch.object(self.backup_file, "get_mtime") as mock_get_mtime:
            mock_get_mtime.return_value = datetime.datetime(2023, 1, 1)
            self.assertTrue(
                self.backup_file.is_older_than_dt(datetime.datetime(2023, 1, 2))
            )
            self.assertFalse(
                self.backup_file.is_older_than_dt(datetime.datetime(2022, 12, 31))
            )

    def test_is_older_than_delta(self):
        """Test that is_older_than_delta correctly compares times."""
        now = datetime.datetime.now()
        with patch.object(self.backup_file, "get_mtime") as mock_get_mtime:
            mock_get_mtime.return_value = now - datetime.timedelta(days=5)
            self.assertTrue(
                self.backup_file.is_older_than_delta(datetime.timedelta(days=4))
            )
            self.assertFalse(
                self.backup_file.is_older_than_delta(datetime.timedelta(days=6))
            )


class TestNeedsBackup(unittest.TestCase):
    """Tests for needs_*_backup functions."""

    @patch("manage_backups.get_backup_files")
    def test_needs_daily_backup(self, mock_get_backup_files):
        """Test the logic for needing a daily backup."""
        mock_backup = MagicMock()
        mock_backup.is_older_than_delta.return_value = True
        mock_get_backup_files.return_value = [mock_backup]
        self.assertTrue(manage_backups.needs_daily_backup())

        mock_backup.is_older_than_delta.return_value = False
        self.assertFalse(manage_backups.needs_daily_backup())

        mock_get_backup_files.return_value = []
        self.assertTrue(manage_backups.needs_daily_backup())

    @patch("manage_backups.get_backup_files")
    def test_needs_weekly_backup(self, mock_get_backup_files):
        """Test the logic for needing a weekly backup."""
        mock_backup = MagicMock()
        mock_backup.is_older_than_delta.return_value = True
        mock_get_backup_files.return_value = [mock_backup]
        self.assertTrue(manage_backups.needs_weekly_backup())

        mock_backup.is_older_than_delta.return_value = False
        self.assertFalse(manage_backups.needs_weekly_backup())

    @patch("manage_backups.get_backup_files")
    def test_needs_monthly_backup(self, mock_get_backup_files):
        """Test the logic for needing a monthly backup."""
        mock_backup = MagicMock()
        mock_backup.is_older_than_delta.return_value = True
        mock_get_backup_files.return_value = [mock_backup]
        self.assertTrue(manage_backups.needs_monthly_backup())

        mock_backup.is_older_than_delta.return_value = False
        self.assertFalse(manage_backups.needs_monthly_backup())


class TestGetNewBackupFilename(unittest.TestCase):
    """Tests for get_new_backup_filename."""

    @patch("manage_backups.datetime")
    def test_with_gametime(self, mock_datetime):
        """Test filename generation with gametime."""
        mock_now = datetime.datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.datetime.now.return_value = mock_now
        filename = manage_backups.get_new_backup_filename("12345")
        self.assertEqual(filename, "backup-20230101-120000-g12345.tar.gz")

    @patch("manage_backups.datetime")
    def test_without_gametime(self, mock_datetime):
        """Test filename generation without gametime."""
        mock_now = datetime.datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.datetime.now.return_value = mock_now
        filename = manage_backups.get_new_backup_filename(None)
        self.assertEqual(filename, "backup-20230101-120000.tar.gz")


class TestGetMinecraftGametime(unittest.TestCase):
    """Tests for get_minecraft_gametime."""

    @patch("manage_backups.subprocess.run")
    def test_success(self, mock_run):
        """Test successful parsing of gametime."""
        mock_result = MagicMock()
        mock_result.stdout = "The time is 1957699916"
        mock_run.return_value = mock_result
        gametime = manage_backups.get_minecraft_gametime()
        self.assertEqual(gametime, "1957699916")
        mock_run.assert_called_once_with(
            ["/srv/minecraft/scripts/rcon.sh", "time query gametime"],
            capture_output=True,
            text=True,
            check=True,
        )

    @patch("manage_backups.subprocess.run")
    def test_parse_failure(self, mock_run):
        """Test failure to parse gametime from output."""
        mock_result = MagicMock()
        mock_result.stdout = "Some unexpected output"
        mock_run.return_value = mock_result
        with self.assertLogs(level="WARNING") as cm:
            gametime = manage_backups.get_minecraft_gametime()
            self.assertIsNone(gametime)
            self.assertIn(
                "Could not parse gametime from: Some unexpected output", cm.output[0]
            )

    @patch("manage_backups.subprocess.run", side_effect=FileNotFoundError)
    def test_file_not_found(self, mock_run):
        """Test FileNotFoundError when rcon script is missing."""
        with self.assertLogs(level="WARNING") as cm:
            gametime = manage_backups.get_minecraft_gametime()
            self.assertIsNone(gametime)
            self.assertIn("`/srv/minecraft/scripts/rcon.sh` not found", cm.output[0])

    @patch(
        "manage_backups.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "cmd"),
    )
    def test_called_process_error(self, mock_run):
        """Test CalledProcessError from the subprocess."""
        with self.assertLogs(level="WARNING") as cm:
            gametime = manage_backups.get_minecraft_gametime()
            self.assertIsNone(gametime)
            self.assertIn("Error getting gametime", cm.output[0])


class TestCreateBackup(unittest.TestCase):
    """Tests for create_backup."""

    @patch("manage_backups.start_minecraft_server")
    @patch("manage_backups.subprocess.run")
    @patch("manage_backups.stop_minecraft_server")
    @patch("manage_backups.get_minecraft_gametime")
    @patch("manage_backups.get_new_backup_filename")
    def test_create_backup_flow(
        self,
        mock_get_filename,
        mock_get_gametime,
        mock_stop_server,
        mock_run,
        mock_start_server,
    ):
        """Test the entire backup creation flow."""
        mock_get_gametime.return_value = "fake_gametime"
        mock_get_filename.return_value = "fake_backup_name.tar.gz"
        parent_dir = MagicMock(spec=pathlib.Path)
        parent_dir.__truediv__.return_value = "/fake/path/fake_backup_name.tar.gz"

        result = manage_backups.create_backup(parent_dir)

        mock_get_gametime.assert_called_once()
        mock_stop_server.assert_called_once()
        mock_get_filename.assert_called_once_with("fake_gametime")
        mock_run.assert_called_once_with(
            ["tar", "-czhf", "/fake/path/fake_backup_name.tar.gz", "/srv/minecraft/current"],
            check=True,
        )
        mock_start_server.assert_called_once()
        self.assertIsInstance(result, manage_backups.BackupFile)
        self.assertEqual(
            result.path, pathlib.Path("/fake/path/fake_backup_name.tar.gz")
        )


class TestDeleteBackups(unittest.TestCase):
    """Tests for backup deletion functions."""

    @patch("manage_backups.get_backup_files")
    def test_delete_backups_older_than_delta(self, mock_get_backup_files):
        """Test the logic for deleting old backups."""
        mock_old_backup = MagicMock()
        mock_old_backup.is_older_than_delta.return_value = True
        mock_new_backup = MagicMock()
        mock_new_backup.is_older_than_delta.return_value = False

        mock_get_backup_files.return_value = [mock_old_backup, mock_new_backup]
        parent_dir = MagicMock(spec=pathlib.Path)
        delta = datetime.timedelta(days=1)

        # Suppress logging output for clean test run
        logging.disable(logging.CRITICAL)
        manage_backups.delete_backups_older_than_delta(parent_dir, delta)
        logging.disable(logging.NOTSET)

        mock_old_backup.path.unlink.assert_called_once()
        mock_new_backup.path.unlink.assert_not_called()


if __name__ == "__main__":
    unittest.main()