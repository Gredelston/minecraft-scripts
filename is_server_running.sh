#!/usr/bin/bash
#
# Check whether the Minecraft server is currently running.
# Exits with status 0 if the server is running, 1 otherwise.

/srv/minecraft/scripts/query.py status &> /dev/null
exit $?
