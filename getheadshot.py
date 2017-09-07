#!/usr/bin/python3

import subprocess

# apt-get install wkhtmltopdf vncsnapshot
# wkhtmltoimage --width 50 --quality 50 <target> out.out
# vncsnapshot -quality 50 <target> out.jpg

def getheadshot(ip,rand):

  process = subprocess.Popen(["wkhtmltoimage","--width","50","--quality","80","-f","jpg","http://"+ip,"data/nweb."+rand+".headshot.jpg"],stdout=subprocess.PIPE)
  if process.wait() is 0:
    print("seems like http worked")
    return True

  process = subprocess.Popen(["wkhtmltoimage","--width","50","--quality","80","-f","jpg","https://"+ip,"data/nweb."+rand+".headshot.jpg"],stdout=subprocess.PIPE)
  if process.wait() is 0:
    print("seems like https worked")
    return True

  process = subprocess.Popen(["vncsnapshot","-quality","50",ip,"data/nweb."+rand+".headshot.jpg"],stdout=subprocess.PIPE)
  if process.wait() is 0:
    print("seems like vnc worked")
    return True

  print("seems like nothing worked")
  return False
