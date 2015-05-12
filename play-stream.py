# -*- coding: utf-8 -*-

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
from gi.repository import GLib
Gst.init(None)
import sys
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
    try:
        page = requests.head(url)
    except Exception:
        return [url]
    urls = [url]
    if page.headers["content-type"] == "audio/x-scpls":
        urls = getURLsFromPLS(StringIO.StringIO(page.text))    
    if page.headers["content-type"] == "audio/x-mpegurl":
        urls = page.text.split()
    #print urls
    return urls

def onTag(bus, msg):
    global tagFile
    taglist = msg.parse_tag()
    ret, tag = taglist.get_string("title")
    out = ""
    if tag:
        title = ""
        sep = True
        for seg in tag.encode("utf-8").replace("&", "and").split("  "):
            if (len(seg.strip()) == 0):
                if sep:
                    title += "-"
                    sep = False
                continue
            title += seg + " "
        segments = title.split("***")
        if(len(segments) > 0):
            out = segments[0].strip()
    if not tagFile or not out:
        return
    try:
        with open(tagFile, "w") as of:
            of.write(out)
    except:
        pass
    
def onMessage(bus, message):
    if not message:
        return
    t = message.type
    if t == Gst.MessageType.TAG:
        onTag(bus, message)
    if t == Gst.MessageType.EOS:
        pass

def playStream(url, onTag):
    #creates a playbin (plays media form an uri) 
    player = Gst.ElementFactory.make("playbin", "player")

    #set the uri
    player.set_property('uri', url)

    #start playing
    #player.set_property("volume", 0)
    player.set_state(Gst.State.PLAYING)

    #listen for tags on the message bus; tag event might be called more than once
    bus = player.get_bus()
    bus.enable_sync_message_emission()
    bus.add_signal_watch()
    bus.connect('message::tag', onTag)
    bus.connect("message", onMessage)
    mainloop = GLib.MainLoop()
    mainloop.run()    
    

def run():
    import argparse
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-s", dest="stationName", metavar="station", help="station name", default="")
    argParser.add_argument("-t", dest="tagFile", help="The current tag in the stream will be written here.", default=None)
    argParser.add_argument("-p", dest="playlist", action="store_true", default=False)
    argParser.add_argument("uri", help="uri of stream")
    args, unknown = argParser.parse_known_args(sys.argv[1:])
    #print args
    #print unknown
    #if len(sys.argv) != 4:
    #    print "ERROR: Invalid number of arguments."
    #    exit(1)
    uri = getEntriesFromPlaylist(args.uri)[0]
    #setup(args.stationName, uri, args.dir)
    global onTag
    global tagFile
    tagFile = args.tagFile
    playStream(uri, onTag)

url = ""
stationName = ""
workingDir = ""
tagFile = ""

if __name__ == "__main__":
    run()
