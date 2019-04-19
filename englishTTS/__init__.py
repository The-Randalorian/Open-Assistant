import pythoncom

pythoncom.CoInitialize()

import threading, time
from queue import Queue
import pyttsx3
import pyttsx3.voice

services = {}
plugin = {}
core = None
runThread = None
threadActive = False
q = Queue()
voices = []
voiceNames = {}


def _register_(serviceList, pluginProperties):
    global services, plugin, core
    services = serviceList
    plugin = pluginProperties
    core = services["core"][0]
    core.addStart(startThread)
    core.addClose(closeThread)
    core.addLoop(loopTask)

    services["userInterface"][0].addCommands({"say": manualSay, "tts": {"say": manualSay, "setprop": manualSetProperty, "setproperty": manualSetProperty, "set": manualSetProperty}})

def loopTask():
    pass

def startThread():
    global runThread, threadActive
    threadActive = True
    runThread = threading.Thread(target = threadScript)
    runThread.daemon = True
    runThread.start()

def closeThread():
    global runThread, q
    threadActive = False
    q.join()
    runThread.join()

def threadScript():
    global voices, voiceNames
    pythoncom.CoInitialize()
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for voice in voices:
        voiceNames[voice.name] = voice.id
    engine.setProperty('rate', 180)
    v = voiceNames.get("Cortana", None)
    if v != None: #default to cortana, if available
        engine.setProperty("voice", v)
    
    while True:
        command = q.get()
        if command[0] == 0:     # say
            engine.say(command[1], command[2])
            engine.runAndWait()
            q.task_done()
        if command[0] == 1:     # set property
            engine.setProperty(command[1], command[2])

def manualSay(arguments):
    """
INFO
    Causes the Text-To-Speech engine to say something.

USAGE
    {0} [phrase]
        phrase - Phrase the TTS engine should say.
    """
    arguments.pop(0)
    say(fixArgs(arguments))

def manualSetProperty(arguments):
    """
INFO
    Sets a property for the Text-To-Speech engine.

USAGE
    {0} [property] [value]
        property - Property to change. This is normally voice, volume or rate.
        value - Value to set. Voice requires a name/ID. Rate requires an integer. Volume requires a decimal.
    """
    global voiceNames
    prop = arguments[1]
    arguments.pop(0)
    arguments.pop(0)
    value = fixArgs(arguments)
    if prop.lower() == "voice":
        v = voiceNames.get(value, None)
        if v != None:
            value = v
    elif prop.lower() == "rate":
        value = int(value)
    elif prop.lower() == "volume":
        value = float(value)
    setProperty(prop.lower(), value)

def fixArgs(arguments):
    s = ""
    for arg in arguments:
        if isinstance(arg, str):
            s += " " + arg
        else:
            s += " " + ".".join(arg)
    s = s.strip()
    return s

#===================================================================
#           Standard TTS functions
#===================================================================

def setProperty(prop, value):
    global q
    q.put([1, prop, value])

def setVolume(value):
    setProperty("volume", value)

def setRate(value):
    setProperty("rate", value)

def setVoice(value):
    setProperty("volume", value)

def say(text, notification="Open Assistant"):
    global q
    q.put([0, text, notification])
