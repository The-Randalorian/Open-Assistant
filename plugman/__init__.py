import threading, time
import sys, os
import urllib.request

services = {}
plugin = {}
core = None
terminal = None
runThread = None
threadActive = False

def _register_(serviceList, pluginProperties):
    global services, plugin, core
    services = serviceList
    plugin = pluginProperties
    core = services["core"][0]
    terminal = services["userInterface"][0]

    terminal.addCommands({"get": get, "plugman": {"get": get}})
    #core.addStart(startThread)
    #core.addClose(closeThread)
    #core.addLoop(loopTask)

def loopTask():
    pass

def startThread():
    global runThread
    threadActive = True
    runThread = threading.Thread(target = threadScript)
    runThread.start()

def closeThread():
    global runThread
    threadActive = False
    runThread.join()

def threadScript():
    global threadActive
    threadActive = False

def get(arguments):
    if len(arguments) > 1:
        arguments.pop(0)
        for i in arguments:
            if isinstance(i, list):
                i = ".".join(i)
            if i[-4:] == ".apm" or i[-4:] == ".apc":
                print("getting " + i + "   ", end="")
                urllib.request.urlretrieve(i, sys.path[0] + i[i.rfind("/"):])
                print("done!")
        print("Plugins will be install on restart.")
    
    
