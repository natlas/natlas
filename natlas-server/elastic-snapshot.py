#!/usr/bin/env python3

from elasticsearch import Elasticsearch, exceptions
from datetime import datetime
import argparse

def main():
	parser_desc = "Server-side utility for creating and restoring elastic snapshots. NOTE: Be sure to set path.repo in elasticsearch.yml before attempting to use this tool."
	parser_epil = "Be sure that you're running this from within the virtual environment for the server."
	parser = argparse.ArgumentParser(description=parser_desc, epilog=parser_epil)
	exgroup = parser.add_mutually_exclusive_group(required=True) # we need to specify either create or restore
	parser.add_argument("-r", "--repo", metavar='REPO', help="Name of the repository to store our snapshot in", default="natlas_backups")
	parser.add_argument("-s", "--snapshot", metavar='SNAPSHOT', help="Name of the snapshot", default="snapshot-")
	parser.add_argument("-e", "--elastic", metavar="URL", help="URL to Elastic cluster", default="http://localhost:9200")
	parser.add_argument("-l", "--location", metavar="PATH",
						help="A path matching one of the paths defined as path.repo in /etc/elasticsearch/elasticsearch.yml",
						default="/tmp/natlas")
	exgroup.add_argument("--restore", action='store_true', default=False, help="If you pass this flag, we will attempt to restore the snapshot named by --snapshot")
	exgroup.add_argument('--create', action='store_true', default=False, help="Create a new snapshot")
	exgroup.add_argument("--list", action='store_true', default=False, help="List existing snapshots to restore from")
	args = parser.parse_args()

	es = Elasticsearch(args.elastic)

	if args.create:
		body = {"type": "fs",
				"settings": {
							"location": args.location
							}
				}
		print("[+]Checking to see if repository named %s exists" % args.repo)
		try:
			print(es.snapshot.get_repository(args.repo))
		except Exception:
			print("[+]Creating Repository named: %s" % args.repo)
			print(es.snapshot.create_repository(args.repo, body, verify=True))
			print("[+]Repository Information: %s" % args.repo)
			print(es.snapshot.get_repository(args.repo))
		if args.snapshot == "snapshot-":
			snapshot_name = args.snapshot + datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
		else:
			snapshot_name = args.snapshot
		print("[+]Creating Snapshot named %s. This may take a while..." % snapshot_name)
		print(es.snapshot.create(args.repo, snapshot_name, wait_for_completion=True))
		print("[+]Getting details for snapshot named %s" % snapshot_name)
		print(es.snapshot.get(args.repo, snapshot_name, verbose=True))
	if args.list:
		print("[+]Listing repositories and snapshots")
		repositories = es.snapshot.get_repository("*")
		for item in repositories:
			print("-%s" % item)
			snapshots = es.snapshot.get(item, "*")
			for snap in snapshots["snapshots"]:
				print("--%s" % snap["snapshot"])
	if args.restore:
		print("[+] Checking to see if repository named %s exists" % args.repo)
		try:
			repo = es.snapshot.get_repository(args.repo)
		except Exception:
			print("[!] Repository %s doesn't exist!" % args.repo)
			return
		print("[+] Checking to see if snapshot named %s exists" % args.snapshot)
		try:
			snapshot = es.snapshot.get(args.repo, args.snapshot)
		except Exception:
			print("[!] Snapshot %s doesn't exist in repo %s!" % (args.snapshot, args.repo))
			return
		print("[+] Attempting to close relevant indices")
		for index in snapshot["snapshots"][0]["indices"]:
			try:
				closed = es.indices.close(index)
				print("[+] Closed %s" % index)
			except exceptions.NotFoundError:
				print("[-] %s doesn't exist, no need to close it" % index)
			except Exception:
				print("[!] We couldn't close index %s" % index)
				return
		print("[+] Attempting to restore snapshot %s. This may take a while..." % args.snapshot)
		print(es.snapshot.restore(args.repo, args.snapshot, wait_for_completion=True))


if __name__ == "__main__":
	main()