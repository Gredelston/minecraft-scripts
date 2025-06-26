#!/srv/minecraft/scripts/mcstatus.venv/bin/python3

"""Retrieve basic info from the server's query port."""

import argparse
import enum

import mcstatus

class Command(enum.Enum):
    PING = "ping"
    STATUS = "status"
    QUERY = "query"
    WHO = "who"

parser = argparse.ArgumentParser()
parser.add_argument(
    "command",
    nargs="?",
    choices=[cmd.value for cmd in Command],
    default=Command.QUERY.value,
)
args = parser.parse_args()

server = mcstatus.JavaServer("minecraft.gredelston.cool")

match args.command:
    case Command.PING.value:
        print(server.ping())
    case Command.STATUS.value:
        print(server.status())
    case Command.QUERY.value:
        print(server.query().raw)
    case Command.WHO.value:
        print(server.query().players.names)
    case _:
        raise ValueError(args.command)
