import json
import typing
from datetime import datetime

import click
from flask.cli import AppGroup

from app import db
from app.models import ScopeItem

cli_group = AppGroup("scope")

import_helptext = "Import scope/blacklist from a file containing line-separated IPs and CIDR ranges. \
Optionally, each line can contain a comma separated list of tags to apply to that target. e.g. 127.0.0.1,local,private,test"


def import_scope(scope_file: typing.TextIO, blacklist: bool):
    if not scope_file:
        return {"failed": 0, "existed": 0, "successful": 0}
    addresses = scope_file.readlines()
    result = ScopeItem.import_scope_list(addresses, blacklist)
    db.session.commit()

    return result


@cli_group.command("import", help=import_helptext)
@click.argument("file", type=click.File("r"))
@click.option(
    "--blacklist/--scope",
    "import_as_blacklist",
    default=False,
    help="Should this file be considered in scope or blacklisted?",
)
def import_items(file: str, import_as_blacklist: bool):
    import_name = "blacklist" if import_as_blacklist else "scope"
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        import_name: import_scope(file, import_as_blacklist),
    }
    print(json.dumps(results, indent=2))


@cli_group.command("export")
def export_items():
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "scope": [
            {
                "target": item.target,
                "blacklist": item.blacklist,
                "tags": item.get_tag_names(),
            }
            for item in ScopeItem.getScope()
        ],
        "blacklist": [
            {
                "target": item.target,
                "blacklist": item.blacklist,
                "tags": item.get_tag_names(),
            }
            for item in ScopeItem.getBlacklist()
        ],
    }
    print(json.dumps(result, indent=2))
