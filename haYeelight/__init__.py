import threading, time
import yeelight
import json

services = {}
plugin = {}
core = None

runThread = None
threadActive = False

lights = []
light_data = []

def _register_(serviceList, pluginProperties):
    global services, plugin, core, ha, lights, light_data
    global YeelightSmartLight
    services = serviceList
    plugin = pluginProperties
    core = services["core"][0]
    actions = services["actions"][0]
    #understanding = actions.understanding
    ha = services["homeAutomation"][0]

    class YeelightSmartLight(ha.AutomationSmartLightColor):
        def __init__(self, ip, new_light=True, **kwargs):
            global lights
            super().__init__(**kwargs)
            self.ip = ip
            self.light = len(lights)
            lights.append(yeelight.Bulb(self.ip))
            lights[self.light].auto_on = True
            if new_light:
                light_data.append({"ip": self.ip, "name": self.name})
            with open(__file__[:-11] + "lights.json", "w") as f:
                json.dump(light_data, f)

        def toggleOn(self):
            global lights
            lights[self.light].turn_on()
            return "Okay"

        def toggleOff(self):
            global lights
            lights[self.light].turn_off()
            return "Okay"

        def setColor(self, color):
            global lights
            col = [int(b*255) for b in color]  # super().setColor(root, raw = True)
            lights[self.light].set_rgb(col[0], col[1], col[2])
            return "Okay"

    #vbf.mem["lights"] = YeelightSmartLight("")
    #lightData = yeelight.discover_lights()
    #for i in range(len(lightData)):
        #vbf.mem["yeelightlight"+str(i)] = YeelightSmartLight(lightData[i]["ip"])
    #print(vbf.mem)
    #core.addStart(startThread)
    #core.addClose(closeThread)
    #core.addLoop(loopTask)

    try:
        with open(__file__[:-11] + "lights.json", "r") as f:
            light_data = json.load(f)
        for ld in light_data:
            YeelightSmartLight(ld["ip"], new_light=False, name=ld["name"])
    except FileNotFoundError:
        pass

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
    print("Discovering Lights")
    lightData = yeelight.discover_bulbs()
    if len(lightData) > 0:
        for i in range(len(lightData)):
            print(str(i + 1) + ". ", end="")
            if lightData[i]["capabilities"]["name"] == "":
                print("Unnamed Light")
            else:
                print(lightData[i]["capabilities"]["name"])
        try:
            n = int(input("enter a light number to connect to. ")) - 1
            name = input("what would you like to call it. (recommended: lights) ").lower()
            if n < len(lightData):
                YeelightSmartLight(lightData[i]["ip"], name=name)
        except ValueError as e:
            print("invalid input")
    else:
        print("No lights detected! Make sure they are on and connected to the same network.")
