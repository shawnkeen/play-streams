# -*- coding: utf-8 -*-

import sys
import os
import socket
import streams
from os.path import join as joinPath


def get_file_path(name):
    return os.path.join(RUNDIR, name)


def get_status():
    if not os.path.isfile(get_file_path("pid")):
        return ST_NOSTREAM
    numFileName = get_file_path("number")
    num = 0
    with open(numFileName, "r") as fd:
        try:
            num = int(fd.readline())
        except:
            pass
    return num


def helpString():
    return """commands:
play [num]      play station number num, 0 for stop
stations        list all available stations
status          return the number of the playing station
"""

if __name__ == "__main__":
    import argparse
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-c", dest="configFile",
                           metavar="config",
                           help="config location", default="config")
    argParser.add_argument("-p", dest="port",
                           metavar="port",
                           help="port to listen on", default="8000",
                           required=False)
    args, unknown = argParser.parse_known_args(sys.argv[1:])

    config = streams.Config(args.configFile)

    s = socket.socket()

    host = socket.gethostname()
    try:
        port = int(args.port)
    except:
        print "could not read port number"
        sys.exit(1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", port))

    s.listen(5)

    RUNDIR = "/var/run/streams"
    ST_NOSTREAM = 0

    while True:
        c, addr = s.accept()
        print "connected to", addr

        for line in c.makefile('r'):
            line = line.strip().split()
            print "got line", line
            command = ""
            answer = ""
            if line:
                command = line[0]
            if command == "exit":
                answer = "exit\n"
                break
            elif command == "status":
                status = streams.getStatusFromFiles(config.dirName)
                if not status:
                    answer = "stopped\n"
                else:
                    answer = str(status) + "\n"
            elif command == "help":
                answer = helpString()
            elif command == "play":
                if len(line) < 2:
                    answer = "no station number given"
                else:
                    try:
                        num = int(line[1])
                        pidFile = joinPath(config.dirName, "pid")
                        if num > 0:
                            station = config.stations[num]
                            tagFile = joinPath(config.dirName, "tag")
                            popen = streams.startPlayer(config.player,
                                                        station,
                                                        tagFile,
                                                        pidFile)
                            if popen:
                                status = streams.Status(station,
                                                        num,
                                                        popen.pid)
                                status.writeToFile(config.dirName)
                        else:
                            streams.killOld(pidFile)
                            answer = "stopped\n"
                    except Exception as e:
                        print e
                        answer = "invalid station number\n"
            elif command == "stations":
                answer = ""
                for i in xrange(1, len(config.stations)):
                    station = config.stations[i]
                    if not isinstance(station, str):
                        answer += str(i) + "  " + station.name + "\n"
            elif command == "":
                answer = ""
            else:
                answer = "could not understand\n"

            if answer:
                c.send(answer)

        print addr, "disconnected"
        c.close()

    s.close()
