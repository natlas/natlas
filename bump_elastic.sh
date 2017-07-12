# run this if the default result window of 10,000 results
# is too low (maximum number of returned search results)

curl -XPUT "http://localhost:9200/nweb/_settings" -d '{ "max_result_window" : 500000 }';
