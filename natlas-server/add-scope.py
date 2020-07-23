#!/usr/bin/env python3
import argparse
from app import create_app, db
from app.models import ScopeItem

app = create_app()
app.app_context().push()


def print_imports(msg, importList):
    if len(importList) > 0:
        print(msg)
        print("\n".join(importList))


def import_scope(file, blacklist, verbose):
    with open(file, "r") as scope:
        addresses = scope.readlines()
    fail, exist, success = ScopeItem.import_scope_list(addresses, blacklist)
    db.session.commit()

    summaryMessages = [
        f"{len(success)} successfully imported.",
        f"{len(exist)} already existed.",
        f"{len(fail)} failed to import.",
    ]

    if verbose:
        print_imports("\nSuccessful Imports:", success)
        print_imports("\nAlready Existed:", exist)
        print_imports("\nFailed Imports:", fail)
    print("\n".join(summaryMessages))


def main():
    helptext = "A file containing line-separated IPs and CIDR ranges to be added to the {}. \
    Optionally, each line can contain a comma separated list of tags to apply to that target. e.g. 127.0.0.1,local,private,test"
    parser_desc = "Server-side utility for populating scope/blacklist from a file directly to the database."
    parser_epil = "Be sure that you're running this from within the virtual environment for the server."
    parser = argparse.ArgumentParser(description=parser_desc, epilog=parser_epil)
    parser.add_argument("--scope", metavar="FILE", help=helptext.format("scope"))
    parser.add_argument(
        "--blacklist", metavar="FILE", help=helptext.format("blacklist")
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Print list of successful, already existing, and failed imports.",
    )
    args = parser.parse_args()

    if args.scope:
        import_scope(args.scope, False, args.verbose)

    if args.blacklist:
        import_scope(args.blacklist, True, args.verbose)


if __name__ == "__main__":
    main()
