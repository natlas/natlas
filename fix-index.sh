mysql -unweb -pnweb --database nweb -e ALTER TABLE scan_manager_host ADD FULLTEXT index_name(data);
