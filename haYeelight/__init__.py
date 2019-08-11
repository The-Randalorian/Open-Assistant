import threading, time
import yeelight

services = {}
plugin = {}
core = None

runThread = None
threadActive = False

bulbs = []

def _register_(serviceList, pluginProperties):
    global services, plugin, core, ha
    global YeelightSmartBulb
    services = serviceList
    plugin = pluginProperties
    core = services["core"][0]
    actions = services["actions"][0]
    vbf = actions.vbf
    ha = services["homeAutomation"][0]

    class YeelightSmartBulb(ha.AutomationSmartBulb):
        def __init__(self, ip, a={}):
            global bulbs
            super().__init__(a)
            self.ip = ip
            self.setCommand(["set", "color"], self.setColor)
            self.bulb = len(bulbs)
            bulbs.append(yeelight.Bulb(self.ip))
            bulbs[self.bulb].auto_on = True

        def turnOn(self, root, *args, **kwargs):
            global bulbs
            bulbs[self.bulb].turn_on()
            return "Okay"

        def turnOff(self, root, *args, **kwargs):
            global bulbs
            bulbs[self.bulb].turn_off()
            return "Okay"

        def setColor(self, root, *args, **kwargs):
            global bulbs
            col = super().setColor(root, raw = True)
            bulbs[self.bulb].set_rgb(col[0], col[1], col[2])
            return "Okay"

    #vbf.mem["lights"] = YeelightSmartBulb("")
    #bulbData = yeelight.discover_bulbs()
    #for i in range(len(bulbData)):
        #vbf.mem["yeelightbulb"+str(i)] = YeelightSmartBulb(bulbData[i]["ip"])
    #print(vbf.mem)
    #core.addStart(startThread)
    #core.addClose(closeThread)
    #core.addLoop(loopTask)

    services["userInterface"][0].addCommands({"yeelight":{"connect": textConnect}})

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

def textConnect(arguments):
    """
INFO
    Setup a connection to a new yeelight

USAGE
    {0}
    """
    print("Discovering Bulbs")
    bulbData = yeelight.discover_bulbs()
    if len(bulbData) > 0:
        for i in range(len(bulbData)):
            print(str(i + 1) + ". ", end="")
            if bulbData[i]["capabilities"]["name"] == "":
                print("Unnamed Bulb")
            else:
                print(bulbData[i]["capabilities"]["name"])
        try:
            n = int(input("enter a bulb number to connect to. ")) - 1
            name = input("what would you like to call it. (recommended: lights) ").lower()
            if n < len(bulbData):
                services["actions"][0].vbf._open()
                services["actions"][0].vbf.mem[name] = YeelightSmartBulb(bulbData[i]["ip"])
                services["actions"][0].vbf._close()
        except ValueError as e:
            print("invalid input")
    else:
        print("No bulbs detected! Make sure they are on and connected to the same network.")
    
