# -*- coding: utf-8 -*-

from gi.repository import GObject
from gi.repository import Gst
import gst
import sys
import gobject
import os
import requests
import ConfigParser
import StringIO

def getURLsFromPLS(fp):
    out = []
    config = ConfigParser.ConfigParser()
    try:
        config.readfp(fp)
        section = "playlist"
        for option in config.options(section):
            if option.startswith("file"):
                out.append(config.get(section, option))
    except Exception as e:
        print e
        pass
    return out

def getEntriesFromPlaylist(url):
    #print "get"
    if url.startswith("mms:"):
        return [url]	
    page = requests.get(url)
    urls = [url]
    if page.headers["content-type"] == "audio/x-scpls":
        urls = getURLsFromPLS(StringIO.StringIO(page.text))    
    if page.headers["content-type"] == "audio/x-mpegurl":
        urls = page.text.split()
    #print urls
    return urls

def onTag(bus, msg):
    global tagFile
    stream_tags = {}
    taglist = msg.parse_tag()
    for key in taglist.keys():
        stream_tags[key] = taglist[key]
    out = ""
    #print stream_tags
    if 'title' in stream_tags:
        title = ""
        sep = True
        for seg in stream_tags['title'].encode("utf-8").replace("&", "and").split("  "):
            if (len(seg.strip()) == 0):
                if sep:
                    title += "-"
                    sep = False
                continue
            title += seg + " "
        segments = title.split("***")
        if(len(segments) > 0):
            out = segments[0].strip()
    try:
        with open(tagFile, "w") as of:
            of.write(out)
    except:
        pass
    
def onMessage(bus, message):
    t = message.type
    if t == Gst.MessageType.TAG:
        onTag(bus, message)
    if t == Gst.MessageType.EOS:
        pass

def playStream(url, onTag):
    #creates a playbin (plays media form an uri) 
    player = gst.element_factory_make("playbin", "player")

    #set the uri
    player.set_property('uri', url)

    #start playing
    #player.set_property("volume", 0)
    player.set_state(gst.STATE_PLAYING)

    #listen for tags on the message bus; tag event might be called more than once
    bus = player.get_bus()
    bus.enable_sync_message_emission()
    bus.add_signal_watch()
    bus.connect('message::tag', onTag)
    bus.connect("message", onMessage)
    mainloop = gobject.MainLoop()
    mainloop.run()    
    

def run():
    import argparse
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-s", dest="stationName", metavar="station", help="station name", default="")
    argParser.add_argument("-d", dest="dir", help="directory for pid file, etc.", default="./")
    argParser.add_argument("-p", dest="playlist", action="store_true", default=False)
    argParser.add_argument("uri", help="uri of stream")
    args, unknown = argParser.parse_known_args(sys.argv[1:])
    #print args
    #print unknown
    #if len(sys.argv) != 4:
    #    print "ERROR: Invalid number of arguments."
    #    exit(1)
    uri = getEntriesFromPlaylist(args.uri)[0]
    setup(args.stationName, uri, args.dir)
    global url
    global onTag
    writeFiles()
    playStream(url, onTag)

def setup(n, u, d):
    global url
    global stationName
    global workingDir
    url = u
    stationName = n
    workingDir = d
        
def writeFiles():    
    global workingDir
    global tagFile
    tagFile = workingDir+"tag"
    pidFile = workingDir+"pid"
    stationFile = workingDir+"station"
    urlFile = workingDir+"url"
    try:
        with open(stationFile, "w") as of:
            of.write(stationName)
        with open(urlFile, "w") as of:
            of.write(url)
        with open(pidFile, "a") as of:
            of.write(str(os.getpid())+"\n")
    except IOError as oe:
        print "ERROR: Could not write to output files: ", str(oe)

url = ""
stationName = ""
workingDir = ""
tagFile = ""

if __name__ == "__main__":
    run()
