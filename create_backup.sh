#!/usr/bin/bash

BACKUPS_DIR="/srv/minecraft/backups"
SERVER_DIR="/srv/minecraft/current"
SCRIPTS_DIR="/srv/minecraft/scripts"

create_backup() {
	DATETIME_FMT="%Y%m%d-%H%M%S"
	DATETIME=$(date +${DATETIME_FMT})
	FILENAME="backup-${DATETIME}.tar.gz"
	BACKUP_PATH="${BACKUPS_DIR}/${FILENAME}"

	echo "Creating backup now."
	sudo tar -czhf ${BACKUP_PATH} -C "/srv/minecraft/" "current"
	if [[ $? -eq 0 ]]; then
		echo "Backup created successfully."
	else
		echo "Backup failed."
		return 1
	fi
}

# TODO: Note whether Minecraft is already running. If not, don't restart at the end.
echo "Stopping Minecraft to create a backup..."
sudo systemctl stop minecraft-server.service

create_backup

echo "Restarting Minecraft..."
sudo systemctl start minecraft-server.service
