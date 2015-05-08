# -*- coding: utf-8 -*-

import ConfigParser
import sys
import subprocess
import os

CONFIG_FILE = "config"

class Station:
    def __init__(self, name, url, playlist):
        self.name = name
        self.url = url
        self.playlist = playlist
    def __str__(self):
        return self.name
        
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
    except IOError:
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
    
if __name__ == "__main__":        
    path = os.path.dirname(os.path.realpath(__file__))
    config = Config(path+"/"+CONFIG_FILE)

    if len(sys.argv) != 2:
        showTag(config)
        exit(0)
        
    try:
        num = int(sys.argv[1])
    except ValueError:
        exit(1)
        
    pidFile = config.dirName+"pid"

    if num == 0:    
        killOld(pidFile)
        osd("off")
        exit(0)
        
    station = config.stations[num]
    killOld(pidFile)
    subprocess.Popen(["/usr/bin/python", path+"/"+config.player, "-s", station.name, station.url, "-d", config.dirName], stderr = sys.stderr, stdout = sys.stdout)
    osd(station.name)