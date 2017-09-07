#!/usr/bin/python3

import subprocess

# wkhtmltoimage --width 50 --quality 50 <target> out.png


def getheadshot(ip,rand):

  process = subprocess.Popen(["wkhtmltoimage","--width","50","--quality","80","-f","jpg","http://"+ip,"data/nweb."+rand+".headshot.jpg"],stdout=subprocess.PIPE)
  if process.wait() is 0:
    print("seems like http worked")
    return True

  process = subprocess.Popen(["wkhtmltoimage","--width","50","--quality","80","-f","jpg","https://"+ip,"data/nweb."+rand+".headshot.jpg"],stdout=subprocess.PIPE)
  if process.wait() is 0:
    print("seems like https worked")
    return True

  print("seems like nothing worked")
  return False
