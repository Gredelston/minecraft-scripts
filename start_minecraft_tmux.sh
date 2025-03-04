#!/bin/bash

if [[ "$(whoami)" != "minecraft-server" ]]; then
	echo "This script must be run by the minecraft-server user."
	exit 1
fi

TMUX=/usr/bin/tmux
SESSION=minecraft-server
RCON=/srv/minecraft/scripts/rcon.sh

is_tmux_session_running() {
	$TMUX has-session -t $SESSION &> /dev/null
	return $?
}

# If the old tmux session is still running, shut it down.
if is_tmux_session_running; then
	echo "Stopping old Minecraft session before starting a new one."
	/srv/minecraft/scripts/stop_minecraft_tmux.sh
fi

# Start a tmux session. systemd should ensure that all environment variables are setup correctly.
echo "Starting new Minecraft session."
$TMUX new-session -d -s $SESSION 'cd /srv/minecraft/current/ && ./run.sh'

# Confirm that the new tmux session is running.
if is_tmux_session_running; then
	echo "Tmux session 'minecraft-server' is running."
else
	echo "Tmux session 'minecraft-server' failed to start."
	exit 1
fi

sleep 5

# Poll until the Minecraft server is running and serving RCON.
interval=2
max_attempts=30
attempts=0
while true; do
	attempts=$((attempts + 1))
	if /srv/minecraft/scripts/is_server_running.sh; then
		echo "Minecraft server is running."
		break
	else
		echo "Minecraft server is not running yet... (attempts=${attempts})"
	fi
	if [ "$attempts" -ge "$max_attempts" ]; then
		echo "Minecraft server failed to start."
		exit 1
	fi
	sleep $interval
done
