# -*- coding: utf-8 -*-

import ConfigParser
import sys
import subprocess
import os
from os.path import join as joinPath


class Station:
    def __init__(self, name, url, playlist):
        self.name = name
        self.url = url
        self.playlist = playlist
    def __str__(self):
        return self.name


class Status:
    def __init__(self, station, number, pid, tag=""):
        self.station = station
        self.pid = str(pid)
        self.number = str(number)
        self.tag = tag

    def writeToFile(self, dir):
        with open(joinPath(dir, "station"), "w") as ff:
            ff.write(self.station.name)
        with open(joinPath(dir, "pid"), "a") as ff:
            ff.write(self.pid+"\n")
        with open(joinPath(dir, "url"), "w") as ff:
            ff.write(self.station.url)
        with open(joinPath(dir, "number"), "w") as ff:
            ff.write(self.number)

    def __str__(self):
        out = ""
        out += self.number
        out += "\n" + str(self.station)
        if self.tag:
            out += "\n" + self.tag
        return out


def getStatusFromFiles(dir):
    try:
        with open(joinPath(dir, "station"), "r") as ff:
            name = ff.readline()
        with open(joinPath(dir, "number"), "r") as ff:
            number = int(ff.readline())
        with open(joinPath(dir, "url"), "r") as ff:
            url = ff.readline()
        with open(joinPath(dir, "pid"), "r") as ff:
            pid = int(ff.readline())
        with open(joinPath(dir, "tag"), "r") as ff:
            tag = ff.readline()
    except IOError as e:
        print e
        return None

    station = Station(name, url, False)
    return Status(station, number, pid, tag)

        
class Config:
    def __init__(self, configFile):
        config = ConfigParser.ConfigParser(defaults = {"playlist" : "yes"})
        config.read(configFile)
        self.stations = ["dummy"]
        try:            
            stationNames = config.get("Global", "stations")
            self.dirName = config.get("Global", "dir").rstrip("/")+"/"
            self.player = config.get("Global", "player")
            for stationName in stationNames.split():
                if not config.has_section(stationName):
                    print "no section", stationName
                    continue
                displayName = config.get(stationName, "name")
                url = config.get(stationName, "url")
                playlist = config.getboolean(stationName, "playlist")
                station = Station(displayName, url, playlist)
                self.stations.append(station)
        except Exception as e:
            print "ERROR Could not read config file "+configFile+":", str(e)
            exit(1)
    

def killOld(pidFile):
    try:
        with open(pidFile, "r") as pidf:
            killed = False
            for line in pidf.readlines():
                pid = int(line.strip())
                try:
                    os.kill(pid, 15)
                    killed = True
                except Exception:
                    pass
        os.remove(pidFile)
    except:
        pass
    

def osd(message):
    cmd = 'echo '+message+' | /usr/bin/aosd_cat --font="Serif 30" -o 1000 -u 400 -R white -f 0 -p 4 -x -640 -y -20'
    os.system(cmd)
    

def showTag(config):
    stationFile = config.dirName+"station"
    tagFile = config.dirName+"tag"
    try:
        with open(stationFile) as sf:
            with open(tagFile) as tf:
                tag = tf.read()
                station = sf.read()    
                cmd = '/usr/bin/notify-send -i gnome-volume-control "'+station+'" "'+tag+'"'
                os.system(cmd)
    except IOError as e:
        print e


def startPlayer(playerFile, station, tagFile, pidFile=None):
    if pidFile:
        killOld(pidFile)
    popen = None
    try:
        with open(tagFile, "w") as ff:
            ff.truncate()
        with open(os.devnull, "w") as devnull:
            popen = subprocess.Popen(["/usr/bin/python", playerFile, "-s", station.name, station.url, "-t", tagFile], close_fds=True, stderr = devnull, stdout = devnull)
    except:
        pass
    return popen


    
if __name__ == "__main__":
    import argparse
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-c", dest="configFile", metavar="config", help="config location", default="")
    argParser.add_argument("-p", dest="playerFile", metavar="player", help="player location", default="")
    argParser.add_argument("-l", dest="listStations", action="store_true", help="list available stations", default=False)
    argParser.add_argument("num", nargs="?", help="station number", default=None)
    args, unknown = argParser.parse_known_args(sys.argv[1:])
    
    currentPath = os.path.dirname(os.path.realpath(__file__))
    configPath = ""

    if not args.configFile:
        configFile = joinPath(currentPath, "config")
    else:
        configFile = args.configFile
        
    config = Config(configFile)

    if args.listStations:
        for i in xrange(1, len(config.stations)):
            print i, config.stations[i]
        exit(0)

    if not args.playerFile:
        playerFile = joinPath(currentPath, config.player)
    else:
        playerFile = args.playerFile

    tagFile = joinPath(config.dirName, "tag")
    pidFile = joinPath(config.dirName, "pid")

    if not args.num:
        showTag(config)
        exit(0)
        
    try:
        num = int(args.num)
    except ValueError:
        exit(1)
        
    if num == 0:    
        killOld(pidFile)
        osd("off")
        exit(0)
        
    station = config.stations[num]

    popen = startPlayer(playerFile, station, tagFile, pidFile)

    if popen:
        status = Status(station, num, popen.pid)
        status.writeToFile(config.dirName)

    osd(station.name)