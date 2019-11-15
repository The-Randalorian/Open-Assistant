import threading, time
from tkinter import Tk, Button

services = {}
plugin = {}
core = None
stt = None
runThread = None
threadActive = False

def _register_(serviceList, pluginProperties):
    global services, plugin, core, stt
    services = serviceList
    plugin = pluginProperties
    core = services["core"][0]
    stt = services["stt"][0]
    core.addStart(startThread)
    core.addClose(closeThread)
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
    global threadActive, stt
    root = Tk("OpenAssistant Trigger")
    def callback():
        rt = threading.Thread(target = stt.trigger())
        rt.start()
    b = Button(root, text="Trigger", command=callback)
    b.pack()
    root.mainloop()
    while threadActive:
        root.update()
    root.destroy()
    threadActive = False
    
