import threading, time

services = {}
plugin = {}
core = None
runThread = None
threadActive = False

def _register_(serviceList, pluginProperties):
    global services, plugin, core
    services = serviceList
    plugin = pluginProperties
    core = services["core"][0]
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
    
