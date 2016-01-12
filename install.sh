#sudo apt-get update
sudo apt-get install python3-pip python3-dev mysql-server libmysqlclient-dev

sudo pip3 install django mysqlclient netaddr

#mysql -uroot -proot -e "CREATE DATABASE nweb CHARACTER SET UTF8;"
#mysql -uroot -proot -e "CREATE USER nweb@localhost IDENTIFIED BY 'nweb';"
#mysql -uroot -proot -e "GRANT ALL PRIVILEGES ON nweb.* TO nweb@localhost;"
#mysql -uroot -proot -e "FLUSH PRIVILEGES;"
