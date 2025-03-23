#!/usr/bin/env python3

"""Create new backups, and delete old backups.

This script is expected to be run on a daily cronjob, but it's OK to run it
manually, too.
"""

import dataclasses
import datetime
import glob
import logging
import pathlib
import subprocess

# Where to find backup files.
BACKUPS_DIR = pathlib.Path("/srv/minecraft/backups")
BACKUPS_DAILY = BACKUPS_DIR / "daily"
BACKUPS_WEEKLY = BACKUPS_DIR / "weekly"
BACKUPS_MONTHLY = BACKUPS_DIR / "monthly"


@dataclasses.dataclass
class BackupFile:
    """An archive that exists on the filesystem."""

    path: pathlib.Path

    def get_mtime(self) -> datetime.timedelta:
        """Get the last-modified time of this archive.

        When working with backup archives, technically we care more about the
        file's birthtime. But since we don't expect the archive's contents to
        change, modified time should be OK. (Note that moving or renaming the
        file updates the file's ctime, but not the mtime.)
        """
        mtime_raw = self.path.stat().st_mtime
        return datetime.datetime.fromtimestamp(mtime_raw)

    # pylint: disable=invalid-name
    def is_older_than_dt(self, dt: datetime.datetime) -> bool:
        """Return whether this archive is older than some datetime."""
        return self.get_mtime() < dt

    def is_older_than_delta(self, delta: datetime.timedelta) -> bool:
        """Return whether this archive is older than some timedelta.

        For the sake of fault-tolerance, delta may be either positive or
        negative. Either way, it is assumed to represent a time in the past.
        """
        return self.is_older_than_dt(datetime.datetime.now() - abs(delta))


def setup_logging() -> None:
    """Setup basic logging."""
    logs_dir = pathlib.Path("/srv/minecraft/backups/logs/")
    logfile_name = datetime.datetime.now().strftime("%Y%m%d-%H%M%S.log")
    logfile_path = logs_dir / logfile_name
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(logfile_path),
        ],
    )


def get_backup_files(root_dir: pathlib.Path) -> list[BackupFile]:
    """Return the backup files in root_dir (non-recursively)."""
    backup_names = glob.glob("**/*.tar.gz", root_dir=root_dir, recursive=True)
    backup_paths = [root_dir / filename for filename in backup_names]
    return [BackupFile(path) for path in backup_paths]


def needs_daily_backup() -> bool:
    """Return whether ~1 day has passed since the last daily backup."""
    daily_backups = get_backup_files(BACKUPS_DAILY)
    # Allow a little wiggle room, since backups are likely created slightly
    # after this script's cron-scheduled runtime.
    max_age = datetime.timedelta(days=1, minutes=-30)
    return all(backup.is_older_than_delta(max_age) for backup in daily_backups)


def needs_weekly_backup() -> bool:
    """Return whether ~1 week has passed since the last daily backup."""
    weekly_backups = get_backup_files(BACKUPS_WEEKLY)
    # Allow a little wiggle room, since backups are likely created slightly
    # after this script's cron-scheduled runtime.
    max_age = datetime.timedelta(weeks=1, minutes=-30)
    return all(backup.is_older_than_delta(max_age) for backup in weekly_backups)


def needs_monthly_backup() -> bool:
    """Return whether ~30 days have passed since the last daily backup."""
    monthly_backups = get_backup_files(BACKUPS_MONTHLY)
    # Allow a little wiggle room, since backups are likely created slightly
    # after this script's cron-scheduled runtime.
    max_age = datetime.timedelta(days=30, minutes=-30)
    return all(backup.is_older_than_delta(max_age) for backup in monthly_backups)


def get_new_backup_filename() -> str:
    """Return the name for a new backup file."""
    return datetime.datetime.now().strftime("backup-%Y%m%d-%H%M%S.tar.gz")


def stop_minecraft_server() -> None:
    """Gracefully stop the Minecraft server."""
    logging.info("Stopping the Minecraft server.")
    subprocess.run(
        ["sudo", "/usr/bin/systemctl", "stop", "minecraft-server.service"],
        check=True,
    )


def start_minecraft_server() -> None:
    """Start the Minecraft server back up."""
    logging.info("Starting the Minecraft server.")
    subprocess.run(
        ["sudo", "/usr/bin/systemctl", "start", "minecraft-server.service"],
        check=True,
    )


def create_backup(parent_dir: pathlib.Path) -> BackupFile:
    """Create a new backup file in parent_dir."""
    stop_minecraft_server()
    backup_path = pathlib.Path(parent_dir / get_new_backup_filename())
    logging.info("Creating backup file: %s", backup_path)
    subprocess.run(
        ["tar", "-czhf", str(backup_path), "/srv/minecraft/current"],
        check=True,
    )
    # TODO: Don't start the server if it didn't need stopping.
    start_minecraft_server()
    return BackupFile(backup_path)


def create_new_backups() -> None:
    """Create new daily, weekly, and monthly backups as needed."""
    if needs_daily_backup():
        create_backup(BACKUPS_DAILY)
    else:
        logging.info("No daily backup needed.")
    if needs_weekly_backup():
        create_backup(BACKUPS_WEEKLY)
    else:
        logging.info("No weekly backup needed.")
    if needs_monthly_backup():
        create_backup(BACKUPS_MONTHLY)
    else:
        logging.info("No monthly backup needed.")


def delete_backups_older_than_delta(
    parent_dir: pathlib.Path,
    delta: datetime.timedelta,
) -> None:
    """Delete any backups in parent_dir older than delta."""
    for backup_file in get_backup_files(parent_dir):
        if backup_file.is_older_than_delta(delta):
            logging.info(
                "Deleting old backup %s (mtime %s is older than %s)",
                backup_file.path,
                backup_file.get_mtime(),
                delta,
            )
            backup_file.path.unlink()


def delete_old_backups() -> None:
    """Delete any old backups daily, weekly, and monthly backups."""
    delete_backups_older_than_delta(BACKUPS_DAILY, datetime.timedelta(days=4))
    delete_backups_older_than_delta(BACKUPS_WEEKLY, datetime.timedelta(weeks=3))
    delete_backups_older_than_delta(BACKUPS_MONTHLY, datetime.timedelta(days=60))


def main() -> None:
    """Create new backups, and delete old backups."""
    setup_logging()
    create_new_backups()
    delete_old_backups()


if __name__ == "__main__":
    main()
