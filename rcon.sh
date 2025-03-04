#!/usr/bin/bash

RCON_DIR=/srv/minecraft/lib/rcon-0.10.3-amd64_linux
RCON_BINARY=${RCON_DIR}/rcon
RCON_CONFIG=${RCON_DIR}/rcon.yaml

$RCON_BINARY -c $RCON_CONFIG "$@"
exit $?
