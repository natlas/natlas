#!/usr/bin/env python3
import argparse
import json
from datetime import datetime
from app import create_app, db
from app.models import ScopeItem


def parse_args():
    helptext = "A file containing line-separated IPs and CIDR ranges to be added to the {}. \
    Optionally, each line can contain a comma separated list of tags to apply to that target. e.g. 127.0.0.1,local,private,test"
    parser_desc = "Server-side utility for populating scope/blacklist from a file directly to the database."
    parser_epil = "This tool does not trigger the running applications to update ScopeManager. \
    Restart the running application or modify the scope via the web panel to trigger the update."
    parser = argparse.ArgumentParser(description=parser_desc, epilog=parser_epil)
    parser.add_argument("--scope", metavar="FILE", help=helptext.format("scope"))
    parser.add_argument(
        "--blacklist", metavar="FILE", help=helptext.format("blacklist")
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Print verbose list of results rather than only the summarized list. Recommend piping this to a file if your inputs are large.",
    )
    args = parser.parse_args()
    if not (args.scope or args.blacklist):
        parser.error("--scope or --blacklist required")
    return args


def import_scope(file: str, blacklist: bool):
    with open(file, "r") as scope:
        addresses = scope.readlines()
    fail, exist, success = ScopeItem.import_scope_list(addresses, blacklist)
    db.session.commit()

    return {"failed": fail, "existed": exist, "successful": success}


def summarize_results(results):
    if not results:
        return {}
    return {
        "failed": len(results["failed"]),
        "existed": len(results["existed"]),
        "successful": len(results["successful"]),
    }


def main(args):
    results = {"summary": {}, "scope": {}, "blacklist": {}}
    if args.scope:
        results["scope"] = import_scope(args.scope, False)

    if args.blacklist:
        results["blacklist"] = import_scope(args.blacklist, True)

    results["summary"] = {
        "timestamp": datetime.utcnow().isoformat(),
        "scope": summarize_results(results["scope"]),
        "blacklist": summarize_results(results["blacklist"]),
    }

    if args.verbose:
        print(json.dumps(results, indent=2))
    else:
        print(json.dumps(results["summary"], indent=2))


if __name__ == "__main__":
    args = parse_args()
    app = create_app()
    with app.app_context():
        main(args)
