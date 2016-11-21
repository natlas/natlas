# Create your models here.

def search(query)
  result=[]
  item={}
  item["ip"]="6.6.6.6"
  item["hostname"]="potato.potato"
  item["ports"]="666"
  item["nmap_data"]="there may be something here some day"
  result.append(item)

  item["ip"]="7.7.7.7"
  item["hostname"]="potato2.potato"
  item["ports"]="777"
  item["nmap_data"]="there will never be anything here"
  result.append(item)

  return result

def newhost(host)
  print("thanks for the new host "+host["hostname"]+" from "+host["ip"])

def gethost(ip)
  item={}
  item["ip"]="8.8.8.8"
  item["hostname"]="potato3.potato"
  item["ports"]="8888"
  item["nmap_data"]="NOOOPE"
  return
