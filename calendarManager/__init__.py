# import threading, time

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
    # core.addStart(startThread)
    # core.addClose(closeThread)
    # core.addLoop(loopTask)


'''
def loopTask():
    pass
'''
'''
def start_thread():
    global runThread
    threadActive = True
    runThread = threading.Thread(target = threadScript)
    runThread.start()

def close_thread():
    global runThread
    threadActive = False
    runThread.join()

def thread_script():
    global threadActive
    threadActive = False
'''
