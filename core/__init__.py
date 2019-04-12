import time, sys





#===============================================================================
#   Create Global Variables
#===============================================================================
services = {}
plugin = {}

startFunctions = []
loopFunctions = []
closeFunctions = []
sanityFunctions = [] #functions to be run at every possible opportunity in the main loop
safetyFunctions = [] #functions to be run in the event of an estop, also called with unsafe

loopOn = True
safe = True #if this value becomes false, the program will end immediately once control is returned
safetyCalled = False

eStopSource = ""




#===============================================================================
#   Define Pre-Run functions
#===============================================================================
class EMERGENCYSTOP(Exception): #Create a custom exception for my purposes
    def __init__(self):    
        self.data = eStopSource
    def __str__(self):
        return repr(self.data)

def _register_(serviceList, pluginProperties):
    services = serviceList
    plugin = pluginProperties
    return True

def eStop(): #eStop will close the program, so dont use it unless you mean it.
    global safetyFunctions, safetyCalled
    eStopSource = sys._getframe().f_back.f_code.co_name
    unsafe()
    if not safetyCalled:
        for function in safetyFunctions:
            function()
        safetyCalled = True
        raise EMERGENCYSTOP
    
def addStart(func):
    global startFunctions
    startFunctions.append(func)

def removeStart(func):
    global startFunctions
    startFunctions.remove(func)
    
def addLoop(func):
    global loopFunctions
    loopFunctions.append(func)

def removeLoop(func):
    global loopFunctions
    loopFunctions.remove(func)

def addClose(func):
    global closeFunctions
    closeFunctions.append(func)

def removeClose(func):
    global closeFunctions
    closeFunctions.remove(func)

def addSanity(func): # I wish I could
    global sanityFunctions
    sanityFunctions.append(func)

def removeSanity(func): # already done
    global sanityFunctions
    sanityFunctions.remove(func)

def addSafety(func):
    global sanityFunctions
    safetyCalled = False
    sanityFunctions.append(func)

def removeSafety(func):
    global safetyFunctions
    safetyFunctions.remove(func)

def stop():
    global loopOn
    loopOn = False

def unsafe():
    global safe
    safe = False





#===============================================================================
#   Define runtime function
#===============================================================================
def _run_():
    global safe, loopOn, startFunctions, loopFunctions, closeFunctions, sanityFunctions, safetyFunctions
    try:
        for function in startFunctions:
            function()
        while loopOn and safe:
            lf = 0
            while lf < len(loopFunctions) and safe:
                loopFunctions[lf]()
                lf += 1
                sf = 0
                while sf < len(sanityFunctions) and safe:
                    sanityFunctions[sf]()
                    sf += 1
            if len(loopFunctions) > 0 and safe:
                time.sleep(0.1)
        cf = 0
        while cf < len(closeFunctions) and safe:
            closeFunctions[cf]()
            cf += 1
    except EMERGENCYSTOP as e:
        raise e
    except Exception as e:
        eStop()
        raise e
    finally:
        if not safe:
            eStop()
    
