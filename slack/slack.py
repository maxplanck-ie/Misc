#!/usr/bin/env python3
import urllib.request
import json
from subprocess import Popen
from time import sleep


def checkUp(path, timeout):
    p = Popen(['ls', path])
    try:
        rc = p.wait(timeout)
    except:
        return False

    if rc is None:
        # Still running! Kill it!
        p.terminate()
        return False
    if rc < 0:
        return False
    return True


def sendMessage(content, channel):
    url = "I need to be set"
    data = json.dumps({"text": content,
                       "username": "nfs-bot",
                       "channel": channel})

    opener = urllib.request.build_opener()
    req = urllib.request.Request(url, data=bytes(data, "ascii"), headers={'Content-Type': 'application/json'})
    resp = opener.open(req)


def iterateStatus(sleepTime, timeout):
    l = [["Void", "/data/processing3", None, "#general"],
         ["Stiff", "/data/galaxy2", None, "#general"],
         ["solsys4", "/data/processing", None, "#general"]]

    while True:
        for _ in l:
            if checkUp(_[1], timeout) is False:
                # NFS is down, only send a message if it was up/unknown
                if _[2] != "down":
                    _[2] = "down"
                    sendMessage("{} is down, time for beer!".format(_[0]), _[3])
            else:
                # NFS is up, don't post if this was already the case
                if _[2] is None:
                    _[2] = "up"
                    sendMessage("Monitoring NFS server {} according to accessibility of {}.".format(_[0], _[1]), _[3])
                elif _[2] == "down":
                    _[2] = "up"
                    sendMessage("{} is risen!".format(_[0]), _[3])
        sleep(sleepTime)


iterateStatus(60*5, 20)
