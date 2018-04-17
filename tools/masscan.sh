masscan --randomize-hosts --include-file ../scope.txt --excludefile ../blacklist.txt -p `cat ../ports.txt` --rate 100000 -oJ masscan.json
