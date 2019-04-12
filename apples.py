#APPLES - Automatic Python Plugin Loading & Executing Script





#===============================================================================
#   Import Libraries
#===============================================================================
import os           #Library used for acessing basic os features
import sys          #Library used for acessing core system features
import importlib    #Library used for dynamically loading libriaries
import configparser #Library used for reading library information
import json         #Library used for reading load order information
import traceback    #Library used for getting error information
#import copy         #Library used for copying info for ordering





#===============================================================================
#   Basic Config
#===============================================================================
LOGLEVEL = 3 # 3 = prints, 2 = warnings, 1 = errors, 0 = crash





#===============================================================================
#   Create Functions
#===============================================================================
class RuleException(Exception): #Create a custom exception for my purposes
    pass #it does nothing special

def loadAPM(file):
    '''
Loads and processes APM files into usable forms
'''
    #Perform initial read
    plugin = configparser.ConfigParser()
    plugin.read(file)

    #Convert to dictionary
    plugin = dict(plugin.items())
    for i, j in plugin.items():
        plugin[i] = dict(j.items())

    #Create dictionary with default values
    plugins.append({
        "properties": {
            "name"      : file,
            "version"   : "0.x.x",
            "service"   : "misc",
            "exclusive" : "no",
            },
        "order"     : {
            "before"    : "[]",
            "after"     : "[]",
            }
        })

    #Update with actual values
    if "properties" in plugin:
        plugins[-1]["properties"].update(plugin["properties"])
    if "order" in plugin:
        plugins[-1]["order"].update(plugin["order"])

    try:
        importlib.import_module(plugin["properties"]["name"]+".precheck")
        #log("\nPre-flight check found for " + plugin["properties"]["name"] + " ", end = "")
    except ModuleNotFoundError:
        #log("precheck not found for " + plugin["properties"]["name"])
        pass
    except Exception as e:
        log("Problem running precheck for " + plugin["properties"]["name"])
        raise e

    #Process json
    plugins[-1]["order"]["before"] = json.loads(plugins[-1]["order"]["before"])
    plugins[-1]["order"]["after"] = json.loads(plugins[-1]["order"]["after"])

def log(string, level=3, end="\n"):
    if level <= LOGLEVEL:
        print(string, end = end)



#===============================================================================
#   Prepare Environment
#===============================================================================
os.chdir(sys.path[0]) #Set program directory
pluginFileExtensions = {
    ".jpp": loadAPM, #.jpp - JukePi Plugin (DEPRECATED)
    ".apm": loadAPM, #.apm - APPLES Plugin Manifest
    }




#===============================================================================
#   Read Module Info
#===============================================================================
log("Identifying plugins...", end = " ")
plugins = []
for file in os.listdir(sys.path[0]):
    if os.path.isfile(os.path.join(sys.path[0], file)):
        for extension in pluginFileExtensions.keys():
            if file[-1*len(extension):].lower() == extension.lower():
                pluginFileExtensions[extension](file)
log("done!")





#===============================================================================
#   Order Plugins
#===============================================================================
log("Ordering plugins...", end = " ")
unsorted = True
while unsorted:
    original = []
    for plugin in plugins:
        original.append(plugin["properties"]["name"])
        
    for plugin in range(0,len(plugins)):
        for target in plugins[plugin]["order"]["after"]:
            if target["plugin"][0] == "$":
                last = 0
                for item in range(0,len(plugins)):
                    if plugins[item]["properties"]["service"] == target["plugin"][1:] and item > plugin:
                        plugins.insert(item + 1, plugins.pop(plugin))
                        break
            else:
                last = 0
                for item in range(0,len(plugins)):
                    if plugins[item]["properties"]["name"] == target["plugin"][0:] and item > plugin:
                        plugins.insert(item + 1, plugins.pop(plugin))
                        break

    unsorted = False
    for plugin in range(0,len(plugins)):
        if original[plugin] != plugins[plugin]["properties"]["name"]:
            unsorted = True
log("done!")





#===============================================================================
#   Load Plugins
#===============================================================================
modules = []
for plugin in plugins:
    log("Loading " + plugin["properties"]["name"] + "...", end = " ")
    modules.append(importlib.import_module(plugin["properties"]["name"]))
    log("done!")





#===============================================================================
#   Create Service List
#===============================================================================
log("Creating list of services...", end = " ")
services = {}
services["*"] = []
for plugin in range(0,len(plugins)):
    services[plugins[plugin]["properties"]["service"]] = services.get(plugins[plugin]["properties"]["service"], []) + [modules[plugin]]
    services["*"].append([modules[plugin]])
log("done!") 





#===============================================================================
#   Register Plugins
#===============================================================================
run = 0
for plugin in range(0,len(plugins)):
    if hasattr(modules[plugin], "_register_"):
        log("Registering services to " + plugins[plugin]["properties"]["name"] + "...", end = " ")
        if modules[plugin]._register_(services, plugins[plugin]):
            run = plugin
            log("Entry point found!", end=" ")
        log("done!")





#===============================================================================
#   Run entry point
#===============================================================================
log("Starting code from entry point!")
try:
    modules[run]._run_()
except Exception as e:
    log("Main thread has crashed with an error. Printing traceback...", 0)
    log(traceback.format_exc(), 0)
    log("Some threads may still be running, but will probably not perform correctly. The main thread will be released when they do.", 0)
    raise e
