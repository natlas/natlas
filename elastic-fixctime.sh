curl -XPUT 'http://localhost:9200/nweb/_mapping/nmap' -d '
{
    "nmap" : {
        "properties" : {
            "ctime" : {"type" : "date" }
        }
    }
}
'
