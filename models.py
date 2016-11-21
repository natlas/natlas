# Create your models here.

def search(query):
  result=[]
  item1={}
  item1["ip"]="6.6.6.6"
  item1["hostname"]="potato.potato"
  item1["ports"]="666"
  item1["nmap_data"]="there may be something here some day"
  result.append(item1)

  item2={}
  item2["ip"]="7.7.7.7"
  item2["hostname"]="potato2.potato"
  item2["ports"]="777"
  item2["nmap_data"]="there will never be anything here"
  result.append(item2)

  return result

def newhost(host):
  print("thanks for the new host "+host["hostname"]+" from "+host["ip"])

def gethost(ip):
  item={}
  item["ip"]="8.8.8.8"
  item["hostname"]="potato3.potato"
  item["ports"]="8888"
  item["nmap_data"]="NOOOPE"
  return item
