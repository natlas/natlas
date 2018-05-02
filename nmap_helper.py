REPORT = "Nmap scan report for "

# Example of what we're looking for in get_ip and get_hostname
# Nmap scan report for 127.0.0.0
# Nmap scan report for something.something.someting.pwn (127.0.0.1)


def get_ip(data):
  for line in data.splitlines():
     if REPORT in line:
       predicate = line.split(REPORT)[1]
       if "(" in predicate:
         return predicate.split(' ')[1][1:-1]
       else:
         return predicate

def get_hostname(data):
  for line in data.splitlines():
    if REPORT in line:
      predicate = line.split(REPORT)[1]
      if "(" in predicate:
        return predicate.split(' ')[0]
      else:
        return predicate

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

