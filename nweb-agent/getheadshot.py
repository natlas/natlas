#!/usr/bin/python3

import subprocess
import os

# wkhtmltoimage --width 50 --quality 80 -f jpg <target> out.jpg
# vncsnapshot -quality 50 <target> out.jpg

def getheadshot(ip,rand, service):

  # display hack, wkhtmltoimage doesn't like to run headless
  # this requires you to run a vncserver or something
  # os.environ["DISPLAY"]=':1'
  if not os.environ["DISPLAY"]:
    return False
  FNULL=open(os.devnull, 'w') # open devnull to get rid of output
  if service in ("vnc"):
    print("[+] (%s) Attempting to take vnc snapshot" % rand)
    process = subprocess.Popen(["vncsnapshot","-quality","50",ip,"data/nweb."+rand+ "." + service + ".headshot.jpg"], stdout=FNULL, stderr=FNULL)
    try:
      out, err = process.communicate(timeout=60)
      if process.returncode is 0:
        return True
    except:
      try:
        print("[+] (%s) Killing slacker process" % rand)
        process.kill()
      except:
        pass

  if service in ("http", "https"):
    print("[+] (%s) Attempting to take %s snapshot" % (rand, service))
    process = subprocess.Popen(["wkhtmltoimage","--javascript-delay","3000","--width","800","--height","600","--quality","80","-f","jpg",service+"://"+ip,"data/nweb."+rand+"." + service + ".headshot.jpg"], stdout=FNULL, stderr=FNULL)
    try:
      out, err = process.communicate(timeout=60)
      if process.returncode is 0:
        return True
    except:
      try:
        print("[+] (%s) Killing slacker process" % rand)
        process.kill()
      except:
        pass

  FNULL.close()
  # fall through to return false if service is unsupported or if process returncodes aren't 0
  return False