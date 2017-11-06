#!/usr/bin/env python3
import urllib.request
import json
from subprocess import Popen, PIPE
from time import sleep
import random


def getFunnyUpperThresh(user):
    """
    These are from nethack
    """
    l = ["The {} attacks the cluster! The attack was poisoned!",
         "The {} kicks the cluster! The cluster slows down!",
         "The {} bites the cluster!",
         "The {} stings the cluster!",
         "The {}'s tentacles suck the cluster!",
         "The {} totally digests the cluster!",
         "The {} hits the cluster! The cluster shudders!"]
    return random.choice(l).format(user)


def getFunnyLowerThresh(user):
    """
    Also from nethack
    """
    l = ["The {} loosens its grip on the cluster!",
         "The {} is vanquished!",
         "The {} lunges toward the cluster and recoils!",
         "The {} turns to run from the cluster!",
         "The {} grabs the cluster, but can not hold on!",
         "The {} is burnt to a crisp!"]
    return random.choice(l).format(user)


def getStatus(cols):
    cols2 = cols.split("/")
    return 100.0 * (int(cols2[0]) + int(cols2[2])) / float(cols2[3])


def sendMessage(content):
    url = "I need to be set"
    data = json.dumps({"text": content,
                       "username": "A level 10 lawful cluster orc",
                       "channel": "#general"})

    opener = urllib.request.build_opener()
    req = urllib.request.Request(url, data=bytes(data, "ascii"), headers={'Content-Type': 'application/json'})
    resp = opener.open(req)


def iterateStatus(sleepTime, thresh0, thresh1, coreThresh):
    """
    sleepTime: Sleep time (in seconds) between iterations
    thresh0: Lower threshold for cluster load.
    thresh1: Upper threshold for cluster load.
    coreThresh: Threshold for number of cores per user
    """
    d = {"bioinfo": None, "Galaxy": None}
    userDict = dict()  # Holds user:cores associations
    slurmState = None

    while True:
        # Is the slurm daemon even up?
        cmd = ['sinfo']
        p = Popen(cmd)
        try:
            rc = p.wait(30)
        except:
            rc = -1
        if rc is None:
            p.terminate()
        if rc < 0 or rc is None:
            if slurmState is not "down":
                sendMessage("Slurm is down, everybody panic!!!")
            slurmState = "down"
            continue
        if slurmState == 'down':
            sendMessage("Slurm is risen, apocalypse averted!!!")
        slurmState = "up"

        # Test for partition-level load
        cmd = ['sinfo', '-o', '"%P %C"']
        p = Popen(cmd, stdout=PIPE)
        so, se = p.communicate()
        so = so.decode("ascii").split("\n")
        for line in so:
            cols = line.strip().split()
            if len(cols) != 2:
                continue
            queueName = cols[0].strip('"')
            if queueName in d:
                s = getStatus(cols[1].strip('"'))
                if d[queueName] is None:
                    d[queueName] = s
                    sendMessage("Monitoring slurm queue {}, the load is currently at {:6.2f}%".format(queueName, s))
                    continue

                if s >= thresh1:
                    if d[queueName] < thresh1:
                        sendMessage("The {} queue is >={:6.2f}% full!".format(queueName, thresh1))
                        d[queueName] = s
                elif s < thresh0:
                    if d[queueName] >= thresh1:
                        sendMessage("The {} queue is now <{:6.2f}% full.".format(queueName, thresh0))
                        d[queueName] = s

        # Test for individual users submitting jobs with excessive core usage
        cmd = ['squeue', '-h', '-o', '"%.15u %.2t %C"', '-p', 'bioinfo']
        p = Popen(cmd, stdout=PIPE)
        so, se = p.communicate()
        so = so.decode("ascii").split("\n")
        userDict2 = dict()
        for line in so:
            cols = line.strip('"').split()
            if len(cols) != 3:
                continue
            if cols[1] != "R":
                continue
            if cols[0] not in userDict2:
                userDict2[cols[0]] = 0
            userDict2[cols[0]] += int(cols[2])
        for k, v in userDict2.items():
            if v > coreThresh:
                if (k in userDict and userDict[k] <= coreThresh/2) or k not in userDict:
                    sendMessage(getFunnyUpperThresh(k))
            elif v <= coreThresh/2:
                if k in userDict and userDict[k] > coreThresh:
                    sendMessage(getFunnyLowerThresh(k))
        #Replace the userDict and make the thresholding simple
        userDict = userDict2
        for k, v in userDict.items():
            if v < coreThresh:
                userDict[k] = coreThresh/2

        sleep(sleepTime)


iterateStatus(60*5, 50, 90, 500)
