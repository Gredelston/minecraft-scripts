# Backup Manager

## Prerequisites

* The Minecraft server must be run through a `systemd` job called `minecraft-server.service`.
* The account running the backup manager must have access to stop and start the `systemd` job.
* If running without a TTY for interactive login, the account running the job must have NOPASSWD access to stop and start the `systemd` job via `/etc/sudoers.d`: for example,
	```
	%minecraft-admins ALL=(root) NOPASSWD: /usr/bin/systemctl start minecraft-server.service
	%minecraft-admins ALL=(root) NOPASSWD: /usr/bin/systemctl stop minecraft-server.service
	```
