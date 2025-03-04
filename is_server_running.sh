#!/usr/bin/bash

/srv/minecraft/scripts/query.py status &> /dev/null
exit $?
