import threading, time
from tkinter import Tk, Button, PhotoImage

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
    root.overrideredirect(1)
    root.config(bg="#151515")
    def callback():
        try:
            rt = threading.Thread(target = stt.trigger())
            rt.start()
        except:
            pass
    b = Button(root, text="Trigger", command=callback, bg="#151515", fg="#3DB8B8")
    photo=PhotoImage(file="tkinterTrigger\logo.png")
    b.config(image=photo,width="200",height="200")
    b.pack()
    root.mainloop()
    while threadActive:
        root.update()
    root.destroy()
    threadActive = False
    
