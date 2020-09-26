#===============================================================================
#   Import Libraries
#===============================================================================
import os               #Library used for acessing basic os features
import sys              #Library used for acessing core system features
#import importlib        #Library used for dynamically loading libriaries
import configparser     #Library used for reading library information
import json             #Library used for reading load order information
#import traceback        #Library used for getting error information
import urllib.request   #Library used for downloading files
#import copy             #Library used for copying info for ordering

import importlib
import pkgutil

import plugman.update_handlers

def iter_namespace(ns_pkg):
    return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")

update_handlers = {
    name.split(".")[-1]: importlib.import_module(name)
    for finder, name, ispkg
    in iter_namespace(plugman.update_handlers)
}

#===============================================================================
#   Basic Config
#===============================================================================
LOGLEVEL = 3 # 3 = prints, 2 = warnings, 1 = errors, 0 = crash





#===============================================================================
#   Create Functions
#===============================================================================

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
    plugin_data = {
        "properties": {
            "name"      : file,
            "version"   : "0.x.x",
            "service"   : "misc",
            "exclusive" : "no",
            },
        "updates"   : {
            "format": "0.0.0",
            "remoteroot": None,
            "localroot" : None,
            "files"     : "[]",
            },
        }

    #Update with actual values
    if "properties" in plugin:
        plugin_data["properties"].update(plugin["properties"])
    if "updates" in plugin:
        plugin_data["updates"].update(plugin["updates"])

    #Replace local directories
    if plugin_data["updates"]["localroot"] != None:
        for key in pathReplacements.keys():
            plugin_data["updates"]["localroot"] = plugin_data["updates"]["localroot"].replace(key, pathReplacements[key])
        
    #Process json
    plugin_data["updates"]["files"] = json.loads(plugin_data["updates"]["files"])
    return plugin_data


def check_for_updates(plugin):
    update_handlers[plugin["updates"]["format"].replace(".", "_")].update_plugin(plugin)



def log(string, level=3, end="\n"):
    if level <= LOGLEVEL:
        print("[updater]: " + string, end=end)

    

#===============================================================================
#   Prepare Environment
#===============================================================================
#os.chdir(sys.path[0]) #Set program directory
pluginFileExtensions = {
    ".jpp": loadAPM, #.jpp - JukePi Plugin (DEPRECATED)
    ".apm": loadAPM, #.apm - APPLES Plugin Manifest
    }
pathReplacements = {
    "_APPLES_": sys.path[0],
    }

#===============================================================================
#   Read Module Info
#===============================================================================
log("Identifying plugins to update...", end = " ")
for file in os.listdir(sys.path[0]):
    if os.path.isfile(os.path.join(sys.path[0], file)):
        for extension in pluginFileExtensions.keys():
            if file[-1*len(extension):].lower() == extension.lower():
                plugin = pluginFileExtensions[extension](file)
                check_for_updates(plugin)
