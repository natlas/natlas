#!/usr/bin/env python

import argparse

from app import create_app
from config import Config
from migrations import migrator

parser_desc = """\
This is a special app instance for developers to generate a new migration without \
going through the full app init process\
"""


def main():

    parser = argparse.ArgumentParser(description=parser_desc)
    parser.add_argument(
        "--message",
        required=True,
        help="Supply a human-readable description of the migration",
    )
    args = parser.parse_args()

    config = Config()
    app = create_app(config, migrating=True)
    migrator.handle_db_migrate(app, args.message)


if __name__ == "__main__":
    main()
