#!/usr/bin/env python3
import argparse
import ipaddress
from app import create_app, db
from app.models import ScopeItem, Tag

app = create_app()
app.app_context().push()

def vprint(msg, verbose):
	if verbose:
		print(msg)



def importScope(file, blacklist, verbose):
	failedImports = []
	alreadyExists = []
	successImports = []
	with open(file, 'r') as scope:
		for line in scope.readlines():
			line = line.strip()
			fail, exist, success = ScopeItem.importScope(line, blacklist)
			failedImports = failedImports + fail
			alreadyExists = alreadyExists + exist
			successImports = successImports + success
	db.session.commit()
	print("%s successfully imported.\n%s already existed.\n%s failed to import." %
			(len(successImports), len(alreadyExists), len(failedImports)))
	if verbose:
		print("\nSuccessful Imports:")
		for i in successImports:
			print("[+] %s" % i)
		print("\nAlready Existed:")
		for i in alreadyExists:
			print("[-] %s" % i)
		print("\nFailed Imports:")
		for i in failedImports:
			print("[!] %s" % i)


def main():
	helptext = "A file containing line-separated IPs and CIDR ranges to be added to the {}. Optionally, each line can contain a comma separated list of tags to apply to that target. e.g. 127.0.0.1,local,private,test"
	parser_desc = "Server-side utility for populating scope/blacklist from a file directly to the database."
	parser_epil = "Be sure that you're running this from within the virtual environment for the server."
	parser = argparse.ArgumentParser(description=parser_desc, epilog=parser_epil)
	parser.add_argument("--scope", metavar='FILE', help=helptext.format("scope"))
	parser.add_argument("--blacklist", metavar='FILE', help=helptext.format("blacklist"))
	parser.add_argument("-v", "--verbose", action="store_true", default=False, help="Print list of successful, already existing, and failed imports.")
	args = parser.parse_args()

	if args.scope:
		importScope(args.scope, False, args.verbose)
	if args.blacklist:
		importScope(args.blacklist, True, args.verbose)

if __name__ == "__main__":
	main()