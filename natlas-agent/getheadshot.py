#!/usr/bin/env python3

import subprocess
import os
import time

# wkhtmltoimage --width 50 --quality 80 -f jpg <target> out.jpg
# vncsnapshot -quality 50 <target> out.jpg


def getheadshot(ip, rand, service):

    # display hack, wkhtmltoimage doesn't like to run headless
    # this requires you to run a vncserver or something
    # os.environ["DISPLAY"]=':1'

    if service in ("vnc"):
        if "DISPLAY" not in os.environ:
            return False
        print("[+] (%s) Attempting to take vnc snapshot" % rand)
        process = subprocess.Popen(["vncsnapshot", "-quality", "50", ip, "data/natlas." +
                                    rand + "." + service + ".headshot.jpg"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        #process = subprocess.Popen(["wkhtmltoimage", "--javascript-delay", "3000", "--width", "800", "--height", "600", "--quality",
        #                            "80", "-f", "jpg", service+"://"+ip, "data/natlas."+rand+"." + service + ".headshot.jpg"], stdout=FNULL, stderr=FNULL)
        p1 = subprocess.Popen(["echo", service+"://"+ip], stdout=subprocess.PIPE)
        process = subprocess.Popen(["aquatone", "-scan-timeout", "1000", "-out", "data/aquatone."+rand+"."+service], stdin=p1.stdout, stdout=subprocess.DEVNULL)
        p1.stdout.close()
        
        try:
            out,err = process.communicate(timeout=60)
            if process.returncode is 0:
                time.sleep(0.5) # a small sleep to make sure all file handles are closed so that the agent can read them
                return True
        except subprocess.TimeoutExpired:
            print("[+] (%s) Killing slacker process" % rand)
            process.kill()
        


    # fall through to return false if service is unsupported or if process returncodes aren't 0
    return False
