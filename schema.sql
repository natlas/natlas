drop table if exists hosts;
create table hosts (
       id integer primary key autoincrement,
       ip text not null,
       ctime integer not null,
       mtime integer not null
);
drop table if exists sightings;
create table sightings (
       id integer primary key autoincrement,
       host_id integer,
       ports text not null,
       hostname txt,
       nmap_data text not null,
       gnmap_data text,
       xml_data text,
       ctime integer not null,
       foreign key(host_id) references hosts(id)
);
drop table if exists sightings_fts;
create virtual table sightings_fts using fts4(content='sightings', nmap_data);
insert into sightings_fts(sightings_fts) values ('REBUILD');
