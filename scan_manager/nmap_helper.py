def get_ip(data):
  # second row, 6th column, cut off parens
  return data.split('\n')[2].split(' ')[5][1:-1]

def get_hostname(data):
  # second row, 5th column
  return data.split('\n')[2].split(' ')[4]

def get_ports(data):
  ports = []
  for line in data.split('\n'):
    try:
      x = int(line.split('/')[0])
    except:
      continue
    if int(x) > 0:
      ports.append(x) # yup, it's a port alright

  return ports
  #return [1,2,3]

def get_country(ip):
  return "fake"

if __name__ == "__main__":
  data = open("sample-output.txt").read()

  print("ip: "+get_ip(data))
  print("hostname: "+get_hostname(data))
  print("ports: "+str(get_ports(data)))

