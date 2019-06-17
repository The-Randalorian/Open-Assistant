import threading, time, re
import yeelight

services = {}
plugin = {}
core = None
actions = None
vbf = None
runThread = None
threadActive = False

def _register_(serviceList, pluginProperties):
    global services, plugin, core, actions, vbf
    global AutomationInterface, AutomationSwitch, AutomationScalar, AutomationSmartBulb
    services = serviceList
    plugin = pluginProperties
    core = services["core"][0]
    actions = services["actions"][0]
    vbf = actions.vbf

    class AutomationInterface(vbf.Thing):
        def __init__(self, a={}):
            self.writeable = False
            self.dataValue = None
            self.dataType = "auto"
            self.pickleable = False
            self.settime = 0
            self.attributes = a
            self.commands = {}

        def setCommand(self, path, function):
            if isinstance(path, str):
                path = [path]
            commandPath = self.commands
            final = path.pop(-1)
            for p in path:
                cp = commandPath.get(p, {})
                commandPath[p] = cp
                commandPath = cp
            commandPath[final] = commandPath.get(final, {})
            commandPath[final]["_"] = function

        def call(self, root, subjects):
            searchPath = [root]
            validPath = []
            searchPath.extend(actions.getDependency(root, u'prep'))
            searchPath.extend(actions.getDependency(root, u'prt'))
            searchPath.extend(actions.getDependency(root, u'dobj'))
            #print(searchPath)

            targets = actions.getDependency(searchPath[-1], u'pobj')
            if len(targets) <= 0:
                targets = actions.getDependency(root, u'dobj')
            target = targets[0].text
            vp = self.commands
            for w in range(0, len(searchPath)):
                if vp.get(searchPath[w].text, None) != None:
                    vp = vp[searchPath[w].text]
                    validPath.append(searchPath[w].text)
            #print(searchPath)
            return self.performAction(root, *validPath)
        
        def performAction(self, root, *args, **kwargs):
            args = list(args)
            commandPath = self.commands
            while len(args) > 0:
                for s in args:
                    cp = commandPath.get(s,{})
                    commandPath[s] = cp
                    commandPath = cp
                    args.remove(s)
            #print(f"{args}: {kwargs}")
            if commandPath.get("_", None) != None and callable(commandPath["_"]):
                return commandPath["_"](root)
            return None

    class AutomationSwitch(AutomationInterface):
        def __init__(self, a={}):
            super().__init__(a)
            self.setCommand(["turn", "on"], self.turnOn)
            self.setCommand(["turn", "off"], self.turnOff)

        def turnOn(self, root, *args, **kwargs):
            return "Default " + type(self).__name__ + " turnOn function. Override me!"

        def turnOff(self, root, *args, **kwargs):
            return "Default " + type(self).__name__ + " turnOff function. Override me!"

    class AutomationScalar(AutomationSwitch):
        def __init__(self, a={}):
            super().__init__(a)
            self.setCommand(["set", "brightness"], self.setLevel)

        def setLevel(self, root, *args, **kwargs):
            try:
                n = actions.getDependency(root, u'prep')[0]
                n = actions.getDependency(n, u'pobj')[0]
                n = actions.getDependency(n, u'nummod')[0]
                return "Default " + type(self).__name__ + " setLevel function. Input was " + n.text + ". Override me!"
            except:
                return "Sorry, I didn't catch what level you want me to set that too."

    class AutomationSmartBulb(AutomationScalar):
        def __init__(self, a={}):
            super().__init__(a)
            self.setCommand(["set", "color"], self.setColor)

        def setColor(self, root, *args, **kwargs):
            raw = kwargs.get("raw", False)
            try:
                n = None
                for color in vbf.mem["colors"].getRawData():
                    n = recursiveSearchText(root, color.getData())
                    if n != None:
                        break
                n = vbf.mem[n.text]
                n = n.parameters['color_rgb']
                if raw:
                    return n
                else:
                    return "Default " + type(self).__name__ + " setColor function. Input was " + str(n) + ". Override me!"
            except KeyError as e:
                if raw:
                    return None
                else:
                    return "Sorry, I didn't catch what color you want me to set that too."

    #vbf.mem["lights"] = AutomationSmartBulb()
    #vbf.vbz["turn"] = vb_action
    
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

def recursiveSearchDep_(root, target):
    if root.dep_ == target:
        return root
    for c in root.children:
        val = None
        val = recursiveSearchDep_(c, target)
        if val != None:
            return val
    return None

def recursiveSearchText(root, target):
    if root.text == target:
        return root
    for c in root.children:
        val = None
        val = recursiveSearchText(c, target)
        if val != None:
            return val
    return None

def vb_action(root, subjects):
    searchPath = [root]
    searchPath.extend(actions.getDependency(root, u'prep'))
    searchPath.extend(actions.getDependency(root, u'prt'))

    targets = actions.getDependency(searchPath[-1], u'pobj')
    if len(targets) <= 0:
        targets = actions.getDependency(root, u'dobj')
    target = targets[0].text
    for w in range(0, len(searchPath)):
        searchPath[w] = searchPath[w].text
    #print(searchPath)
    return vbf.mem[target].performAction(*searchPath)
