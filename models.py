from flask import g
import sqlite3
import os
import random
import re
import time
from datetime import datetime

# Create your models here.

# db hooks

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect('nweb.db')
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'nweb.db'):
        g.nweb_db = connect_db()
        return g.nweb_db

def init_db():
    db = get_db()
    with open('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
        db.commit()

def nmap_to_ip_ctime(nmap):
    """take nmap output and return a ctime and ip parsed from it"""
    firstlines = nmap.splitlines()[:2]
    mo = re.search('scan initiated (.+) as:', firstlines[0])
    c_date = datetime.strptime(mo.group(1), '%a %b %d %H:%M:%S %Y')
    ctime = int(datetime.strftime(c_date, '%s'))
    mo = re.search('Nmap scan report for .* \((.*)\)', firstlines[1])
    ip = mo.group(1)
    return (ip, ctime)

def create_sighting(nmap, gnmap, xml, lie_time=None, lie_ip=None):
    db = get_db()
    (ip, ctime) = nmap_to_ip_ctime(nmap)
    if lie_time:
        ctime = lie_time
    if lie_ip:
        ip = lie_ip
    print("importing scan for %s done at %s" % (ip, ctime))
    sql = 'select id, mtime from hosts where ip = ?'
    cur = db.execute(sql, (ip,))
    row = cur.fetchall()
    if len(row) == 0:
        # need to insert
        sql = 'insert into hosts ' \
              '(ip, ctime, mtime) ' \
              'values (?, ?, ?)'
        cur = db.cursor()
        cur.execute(sql, (ip, ctime, ctime))
        host_id = cur.lastrowid
        mtime = ctime
        print("created host_id %s" % host_id)
    else:
       host_id = row[0][0]
       mtime = row[0][1]
       print("found host_id %s" % host_id)
    sql = 'insert into sightings ' \
          '(host_id, hostname, ports, nmap_data, gnmap_data, xml_data, ctime) ' \
          'values (?, ?, ?, ?, ?, ?, ?)'
    cur = db.cursor()
    cur.execute(sql, (host_id,
                      "not.working", "FIXME NOT IMPLEMENTED",
                      nmap, gnmap, xml,
                      ctime))
    sql = 'insert into sightings_fts(sightings_fts) values ("REBUILD")'
    cur.execute(sql)
    if ctime > mtime:
        # if we're seeing the host at a time later than we have before, update mtime
        sql = 'update hosts SET mtime = ? where id = ?'
        cur.execute(sql, (ctime, host_id))
    db.commit()

def add_corpus():
    """add files in corpus to database"""
    db = get_db()
    files = os.listdir("corpus")
    basenames = set()
    for filename in files:
        basenames.add(filename.split('.')[0])
    for basename in basenames:
        basepath = os.path.join('corpus', basename)
        with open(basepath + '.nmap', "r") as f:
            nmap = f.read()
        try:
            with open(basepath + '.xml', "r") as f:
                xml = f.read()
        except IOError:
            xml = ""
        try:
            with open(basepath + '.gnmap', "r") as f:
                gnmap = f.read()
        except IOError:
            gnamp = ""
        for i in range(0, 100):
            rando_ip = "%d.%d.%d.%d" % (random.randrange(1,254),
                                        random.randrange(1,254),
                                        random.randrange(1,254),
                                        random.randrange(1,254))
            (ip, real_ctime) = nmap_to_ip_ctime(nmap)
            for i in range(0, random.randrange(1, 10)):
                rando_ctime = real_ctime - random.randrange(3600, 3600*24*365)
                create_sighting(nmap, xml, gnmap, rando_ctime, rando_ip)

def search(query,limit,offset):
    sql = 'select ' \
          'hosts.id, hosts.ip, hosts.ctime, hosts.mtime, '\
          'sightings.id, sightings.hostname, sightings.host_id, sightings.ports, '\
          'sightings.nmap_data, sightings.gnmap_data, ' \
          'sightings.xml_data, sightings.ctime '
    if query:
        sql += ',sightings_fts.rowid, sightings_fts.nmap_data '
    sql += 'from hosts ' \
           'inner join sightings on ' \
           'hosts.id = sightings.host_id '
    if query:
        sql += 'inner join sightings_fts on ' \
               'sightings.id = sightings_fts.rowid ' \
               'where sightings.ctime = hosts.mtime ' \
               'and sightings_fts.nmap_data match ? '
    sql += 'order by hosts.mtime desc limit ? offset ?'
    db = get_db()
    cur = None
    start = time.time()
    if query:
        cur = db.cursor().execute(sql, (query,limit,offset))
    else:
        cur = db.cursor().execute(sql)
    entries = cur.fetchall()
    end = time.time()
    print("search took %f seconds" % float(end-start))
    result=[]
    for entry in entries:
        item = {}
        item["ip"] = entry["ip"]
        item["hostname"] = entry["hostname"]
        item["ports"] = entry["ports"]
        item["nmap_data"] = entry["nmap_data"]
        result.append(item)
    return result

def newhost(host):
    db = get_db()
    ip = host["ip"]
    sql = 'select id, mtime from hosts where ip = ?'
    cur = db.execute(sql, (ip,))
    row = cur.fetchall()
    c_time = int(time.time())
    if len(row) == 0:
        # need to insert
        sql = 'insert into hosts ' \
              '(ip, ctime, mtime) ' \
              'values (?, ?, ?)'
        cur = db.cursor()
        cur.execute(sql, (ip, c_time, c_time))
        host_id = cur.lastrowid
        m_time = c_time
    else:
       host_id = row[0][0]
       m_time = row[0][1]
    sql = 'insert into sightings ' \
          '(host_id, hostname, ports, nmap_data, gnmap_data, xml_data, ctime) ' \
          'values (?, ?, ?, ?, ?, ?, ?)'
    cur = db.cursor()
    cur.execute(sql, (host_id,
                      host["hostname"],
                      host["ports"],
                      host["nmap_data"],
                      host["gnmap_data"],
                      host["xml_data"],
                      c_time))
    sql = 'insert into sightings_fts(sightings_fts) values ("REBUILD")'
    cur.execute(sql)
    if c_time > m_time:
        # if we're seeing the host at a time later than we have before, update m_time
        sql = 'update hosts SET mtime = ? where id = ?'
        cur.execute(sql, (c_time, host_id))
    db.commit()
    print("thanks for the new host "+host["hostname"]+" from "+host["ip"])

def gethost(ip):
    #FIXME: this ignore history and that is the whole point
    sql = 'select ' \
          'hosts.*, sightings.* from hosts ' \
          'inner join sightings on ' \
          'hosts.id = sightings.host_id ' \
          'where hosts.ip = ? and sightings.ctime = hosts.mtime'
    db = get_db()
    cur = db.cursor().execute(sql, (ip,))
    entries = cur.fetchall()
    assert len(entries) <= 1
    item = {}
    if len(entries) == 1:
        entry = entries[0]
        item["ip"] = entry["ip"]
        item["hostname"] = entry["hostname"]
        item["ports"] = entry["ports"]
        item["nmap_data"] = entry["nmap_data"]
    return item

#
# Editor modelines  -  https://www.wireshark.org/tools/modelines.html
#
# Local variables:
# c-basic-offset: 4
# indent-tabs-mode: nil
# End:
#
# vi: set shiftwidth=4 expandtab:
# :indentSize=4:noTabs=true:
#
