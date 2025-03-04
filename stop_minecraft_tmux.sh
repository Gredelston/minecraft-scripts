#!/bin/bash

if [[ "$(whoami)" != "minecraft-server" ]]; then
	echo "This script must be run by the minecraft-server user."
	exit 1
fi

TMUX=/usr/bin/tmux
SESSION=minecraft-server
RCON=/srv/minecraft/scripts/rcon.sh

stop_server() {
	echo "Shutting down Minecraft server..."
	$RCON "say SERVER SHUTTING DOWN IN 10 SECONDS..."
	$RCON save-all
	sleep 10
	$RCON stop
	echo "Minecraft server stopped successfully."
}

kill_tmux_session() {
	if $TMUX has-session -t $SESSION 2> /dev/null; then
		echo "Killing minecraft-server tmux session."
		$TMUX kill-session -t $SESSION
	else
		echo "minecraft-server tmux session is not running."
	fi
}

stop_server
kill_tmux_session
