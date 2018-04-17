masscan --randomize-hosts --include-file ../config/scope.txt --excludefile ../config/blacklist.txt -p `cat ../config/ports.txt` --rate 100000 -oJ masscan.json
