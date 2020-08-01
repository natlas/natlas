from datetime import datetime
import json
import typing

import click
from flask.cli import AppGroup

from app import db
from app.models import ScopeItem

cli_group = AppGroup("scope")

import_helptext = "A file containing line-separated IPs and CIDR ranges to be added to the {}. \
Optionally, each line can contain a comma separated list of tags to apply to that target. e.g. 127.0.0.1,local,private,test"


def import_scope(scope: typing.TextIO, blacklist: bool):
    addresses = scope.readlines()
    fail, exist, success = ScopeItem.import_scope_list(addresses, blacklist)
    db.session.commit()

    return {"failed": fail, "existed": exist, "successful": success}


def summarize_import_results(results: dict):
    if not results:
        return {}
    return {
        "failed": len(results["failed"]),
        "existed": len(results["existed"]),
        "successful": len(results["successful"]),
    }


@cli_group.command("import")
@click.option("--scope", type=click.File("r"), help=import_helptext.format("scope"))
@click.option(
    "--blacklist", type=click.File("r"), help=import_helptext.format("blacklist")
)
@click.option(
    "--verbose/--summarize",
    default=False,
    help="Print status of all addresses / ranges instead of only the summary.",
)
def import_items(scope: str, blacklist: str, verbose: bool):
    if not (scope or blacklist):
        raise click.UsageError("--scope or --blacklist is required.")
    results = {"summary": {}, "scope": {}, "blacklist": {}}
    if scope:
        results["scope"] = import_scope(scope, False)

    if blacklist:
        results["blacklist"] = import_scope(blacklist, True)

    results["summary"] = {
        "timestamp": datetime.utcnow().isoformat(),
        "scope": summarize_import_results(results["scope"]),
        "blacklist": summarize_import_results(results["blacklist"]),
    }

    if verbose:
        print(json.dumps(results, indent=2))
    else:
        print(json.dumps(results["summary"], indent=2))


@cli_group.command("export")
def export_items():
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "scope": [
            {"target": item.target, "blacklist": item.blacklist, "tags": item.tags}
            for item in ScopeItem.getScope()
        ],
        "blacklist": [
            {"target": item.target, "blacklist": item.blacklist, "tags": item.tags}
            for item in ScopeItem.getBlacklist()
        ],
    }
    print(json.dumps(result, indent=2))
