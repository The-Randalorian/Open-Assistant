import threading, time
import sys, os
import urllib.request
import json

services = {}
plugin = {}
core = None
terminal = None
runThread = None
threadActive = False
repositoryFormat = "0.1.0"

def _register_(serviceList, pluginProperties):
    global services, plugin, core, repositories
    services = serviceList
    plugin = pluginProperties
    core = services["core"][0]
    terminal = services["userInterface"][0]

    terminal.addCommands({"get": get, "add": addARF, "addARF": addARF, "plugman": {"get": get, "add": addARF, "addARF": addARF}})

    if not os.path.exists('plugman/repositories.acf'):
        with open('plugman/repositories.acf', mode='w') as f:
            f.write("""{
        "format":"0.1.0",
        "repositoryData":{
            "entries":[
            ]
        }
    }""")
    with open('plugman/repositories.acf', mode='r') as f:
        repositories = json.load(f)
    
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
        print("Plugins will be installed on restart.")

def addARF(arguments):
    global repositories
    if len(arguments) > 1:
        arguments.pop(0)
        for i in arguments:
            if isinstance(i, list):
                i = ".".join(i)
            if i[-4:] == ".arf":
                print("Getting " + i + "   ", end="")
                repo = json.load(urllib.request.urlopen(i))
                print("done!")
                if repo["format"] == "0.0.0" or repo["format"] == repositoryFormat:
                    print("Adding " + repo["name"] + " to repositories " + "   ", end="")
                    repositories["repositoryData"]["entries"].append(repo)
                    print("done!")
                
            else:
                print(i + " is not a .arf file. Please change the file extension or notify the repository maintainers of the issue")
