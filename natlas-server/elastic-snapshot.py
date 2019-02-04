#!/usr/bin/env python3

from elasticsearch import Elasticsearch
from datetime import datetime
import argparse

def main():
    parser_desc = "Server-side utility for taking an elastic snapshot"
    parser_epil = "Be sure that you're running this from within the virtual environment for the server."
    parser = argparse.ArgumentParser(description=parser_desc, epilog=parser_epil)
    parser.add_argument("-r", "--repo", metavar='REPO', help="Name of the repository to store our snapshot in", default="natlas_backups")
    parser.add_argument("-s", "--snapshot", metavar='SNAPSHOT', help="Name of the snapshot", default="snapshot-")
    parser.add_argument("-e", "--elastic", metavar="URL", help="URL to Elastic cluster", default="http://localhost:9200")
    parser.add_argument("-l", "--location", metavar="PATH", 
                        help="A path matching one of the paths defined as path.repo in /etc/elasticsearch/elasticsearch.yml",
                        default="/tmp/natlas")
    args = parser.parse_args()

    es = Elasticsearch(args.elastic)
    body = {"type": "fs", 
            "settings": {
                        "location": args.location
                        }
            }

    print("Creating Repository named: %s" % args.repo)
    print(es.snapshot.create_repository(args.repo, body, verify=True))
    print("\nRepository Information: %s" % args.repo)
    print(es.snapshot.get_repository(args.repo))
    snapshot_name = args.snapshot + datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
    print("\nCreating Snapshot named %s" % snapshot_name)
    print(es.snapshot.create(args.repo, snapshot_name, wait_for_completion=True))
    print("\nGetting snapshot named %s" % snapshot_name)
    print(es.snapshot.get(args.repo, snapshot_name, verbose=True))

if __name__ == "__main__":
    main()