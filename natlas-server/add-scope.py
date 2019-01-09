#!/usr/bin/env python
import argparse
import ipaddress
from app import app, db
from app.models import ScopeItem


def importScope(file, blacklist):
    successImport = 0
    alreadyExists = 0
    failedImports = []
    with open(file, 'r') as scope:
        for line in scope.readlines():
            line = line.strip()
            if '/' not in line:
                line = line + '/32'
            try:
                isValid = ipaddress.IPv4Network(line)
            except ValueError as e:
                failedImports.append(e)
                continue
            item = ScopeItem.query.filter_by(target=line).first()
            if item:
                alreadyExists += 1
                continue
            else:
                newTarget = ScopeItem(target=line, blacklist=blacklist)
                db.session.add(newTarget)
                db.session.commit()
                successImport += 1
    print("%s\n-----\n%s successfully imported.\n%s already existed.\nFailed Imports:" %
          (file, successImport, alreadyExists))
    for i in failedImports:
        print("[!] %s" % i)
    print("\n")


parser = argparse.ArgumentParser()
parser.add_argument("--scope")
parser.add_argument("--blacklist")
args = parser.parse_args()
if args.scope:
    importScope(args.scope, False)
if args.blacklist:
    importScope(args.blacklist, True)
