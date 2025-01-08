#!/usr/bin/env python
"""
This is a special app instance that allows us to perform database operations
without going through the app's migration_needed check. Running this script
is functionally equivalent to what `flask db` normally does. The reason we
can't continue to use that is that command is that it invokes the app instance from
FLASK_APP env variable (natlas-server.py) which performs the migration check and exits
during initialization.
"""

import argparse

from app import create_app
from config import Config
from migrations import migrator

parser_desc = """Perform database operations for Natlas.\
It is best practice to take a backup of your database before you upgrade or downgrade, just in case something goes wrong.\
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=parser_desc)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--upgrade",
        action="store_true",
        help="Perform a database upgrade, if necessary",
    )
    group.add_argument(
        "--downgrade",
        action="store_true",
        help="Revert the most recent database upgrade. Danger: This will destroy data as necessary to revert to the previous version.",
    )
    args = parser.parse_args()

    config = Config()
    app = create_app(config, migrating=True)
    if args.upgrade:
        app.config.update({"DB_AUTO_UPGRADE": True})
        migrator.handle_db_upgrade(app)
    elif args.downgrade:
        migrator.handle_db_downgrade(app)


if __name__ == "__main__":
    main()
