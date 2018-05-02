#!/usr/bin/python3

import subprocess
import os

# wkhtmltoimage --width 50 --quality 80 -f jpg <target> out.jpg
# vncsnapshot -quality 50 <target> out.jpg

def getheadshot(ip,rand, service):

  # display hack, wkhtmltoimage doesn't like to run headless
  # this requires you to run a vncserver or something
  # os.environ["DISPLAY"]=':1'

  if service in ("vnc")
    process = subprocess.Popen(["vncsnapshot","-quality","50",ip,"data/nweb."+rand+ "." + service + ".headshot.jpg"],stdout=subprocess.PIPE)
    try:
      out, err = process.communicate(timeout=60)
      if process.returncode is 0:
        return True
    except:
      try:
        print("killing slacker process")
        process.kill()
      except:
        print("okay, seems like it was already dead")

  if service in ("http", "https"):
    process = subprocess.Popen(["wkhtmltoimage","--javascript-delay","3000","--width","800","--height","600","--quality","80","-f","jpg",service+"://"+ip,"data/nweb."+rand+"." + service + ".headshot.jpg"],stdout=subprocess.PIPE)
    try:
      out, err = process.communicate(timeout=60)
      if process.returncode is 0:
        return True
    except:
      try:
        print("killing slacker process")
        process.kill()
      except:
        print("okay, seems like it was already dead")
