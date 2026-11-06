"""Small operator commands.

Usage from the backend directory:

    python -m app.cli reset-admin
"""

from __future__ import annotations

import argparse
import getpass
import sys

from app.config import get_settings
from app.database import init_db, session_scope
from app.services.accounts import set_password


def reset_admin(username: str, password: str) -> None:
    settings = get_settings()
    init_db()
    with session_scope() as db:
        set_password(db, username or settings.admin_username, password)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qubit-api")
    sub = parser.add_subparsers(dest="command", required=True)
    reset = sub.add_parser("reset-admin", help="Set the local administrator password")
    reset.add_argument("--username", default="")
    reset.add_argument("--password", default="")
    args = parser.parse_args(argv)
    if args.command == "reset-admin":
        password = args.password or getpass.getpass("New password: ")
        username = args.username or get_settings().admin_username
        reset_admin(username, password)
        print(f"Password updated for {username}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
