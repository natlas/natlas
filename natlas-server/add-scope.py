#!/usr/bin/env python3
import argparse
import ipaddress
from app import create_app, db
from app.models import ScopeItem

app = create_app()
app.app_context().push()

def importScope(file, blacklist, verbose):
    failedImports = []
    alreadyExists = []
    successImports = []
    with open(file, 'r') as scope:
        for line in scope.readlines():
            line = line.strip()
            if '/' not in line:
                line = line + '/32'
            try:
                isValid = ipaddress.ip_network(line, False) # False will mask out hostbits for us, ip_network for eventual ipv6 compat
            except ValueError as e:
                failedImports.append(line) # if we hit this ValueError it means that the input couldn't be a CIDR range
                continue
            item = ScopeItem.query.filter_by(target=isValid.with_prefixlen).first() # We only want scope items with masked out host bits
            if item:
                alreadyExists.append(isValid.with_prefixlen)
                continue
            else:
                newTarget = ScopeItem(target=isValid.with_prefixlen, blacklist=blacklist)
                db.session.add(newTarget)
                successImports.append(isValid.with_prefixlen)
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
    parser_desc = "Server-side utility for populating scope/blacklist from a file directly to the database"
    parser_epil = "Be sure that you're running this from within the virtual environment for the server."
    parser = argparse.ArgumentParser(description=parser_desc, epilog=parser_epil)
    parser.add_argument("--scope", metavar='FILE', help="A file containing line-separated IPs and CIDR ranges to be added to scope.")
    parser.add_argument("--blacklist", metavar='FILE', help="A file containing line-separated IPs and CIDR ranges to be added to the blacklist.")
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help="Print list of successful, already existing, and failed imports.")
    args = parser.parse_args()

    if args.scope:
        importScope(args.scope, False, args.verbose)
    if args.blacklist:
        importScope(args.blacklist, True, args.verbose)

if __name__ == "__main__":
    main()