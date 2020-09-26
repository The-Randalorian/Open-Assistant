#!/usr/bin/env python3

# APPLES - Automatic Python Plugin Loading & Executing Script

# Version 0.1.3


# =============================================================================
#   Import Libraries
# =============================================================================
import os              # Library used for acessing basic os features
import sys             # Library used for acessing core system features
import importlib       # Library used for dynamically loading libriaries
import configparser    # Library used for reading library information
import json            # Library used for reading load order information
import traceback       # Library used for getting error information
import urllib.request  # Library used for downloading files
# import copy            # Library used for copying info for ordering


# =============================================================================
#   Basic Config
# =============================================================================
LOGLEVEL = 3  # 3 = prints, 2 = warnings, 1 = errors, 0 = crash
pathReplacements = {
    "_APPLES_": sys.path[0],
    "\\": "/"
    }


# =============================================================================
#   Create Functions
# =============================================================================
class RuleException(Exception):  # Create a custom exception for my purposes
    pass  # it does nothing special


def replacePath(local):
    for key in pathReplacements.keys():
        local = local.replace(key, pathReplacements[key])
    return local


def getLocRem(local, remote):
    local = replacePath(local)
    remoteFile = urllib.request.urlopen(remote)
    print(local)
    with open(local, 'wb') as localFile:
        localFile.write(remoteFile.read())


APC_formats = ["0.0.0", "0.1.0"]


def loadAPC(filepath):
    with open(filepath, "r") as file:
        localData = json.load(file)
        if localData.get("format", "0.0.0") in APC_formats:
            try:
                with urllib.request.urlopen(localData["remote"]) as response:
                    remoteData = json.loads(response.read().decode())
                    if remoteData.get("format", "0.0.0") in APC_formats:
                        if localData.get("ver") != remoteData.get("ver"):
                            getLocRem(remoteData["local"],
                                      remoteData["remote"])
            except Exception as e:
                print(e)
    with open(filepath, "r") as file:
        data = json.load(file)
        for entry in data["collection"]:
            if entry["type"].lower() == "file":
                if not os.path.isfile(replacePath(entry["local"])):
                    getLocRem(entry["local"], entry["remote"])
            if entry["type"].lower() == "plugin":
                if not os.path.isfile(replacePath(entry["local"])):
                    getLocRem(entry["local"], entry["remote"])
                    plugin = configparser.ConfigParser()
                    plugin.read(replacePath(entry["local"]))
                    format = plugin["updates"].setdefault("format", "0.0.0")
                    if format == "0.0.0":
                        for pluginDep in json.loads(plugin["updates"]["files"]):
                            pluginDep[0] = plugin["updates"]["localroot"] + pluginDep[0]
                            pluginDep[0] = replacePath(pluginDep[0])
                            if not os.path.isfile(pluginDep[0]):
                                pluginDep[1] = plugin["updates"]["remoteroot"] + pluginDep[1]
                                filepath = pluginDep[0].rsplit("/", 1)[0]
                                if not os.path.exists(filepath):
                                    os.makedirs(filepath)
                                getLocRem(pluginDep[0], pluginDep[1])
                    elif format == "0.1.0":
                        for pluginDep in json.loads(plugin["updates"]["files"]):
                            pluginDep = plugin["updates"]["localroot"] + pluginDep
                            pluginDep = replacePath(pluginDep)
                            if not os.path.isfile(pluginDep):
                                pluginDep = plugin["updates"]["remoteroot"] + pluginDep
                                filepath = pluginDep.rsplit("/", 1)
                                if not os.path.exists(filepath):
                                    os.makedirs(filepath)
                                getLocRem(pluginDep, pluginDep)

            if entry["type"].lower() == "collection":
                if not os.path.isfile(replacePath(entry["local"])):
                    getLocRem(entry["local"], entry["remote"])
                loadAPC(replacePath(entry["local"]))


def loadAPCs():
    for file in os.listdir(sys.path[0]):
        if os.path.isfile(os.path.join(sys.path[0], file)):
            if file[-4:].lower() == ".apc":
                loadAPC(os.path.join(sys.path[0], file))


loadAPCs()


def loadAPM(file):
    '''
Loads and processes APM files into usable forms
'''
    # Perform initial read
    plugin = configparser.ConfigParser()
    plugin.read(file)

    # Convert to dictionary
    plugin = dict(plugin.items())
    for i, j in plugin.items():
        plugin[i] = dict(j.items())

    # Create dictionary with default values
    plugins.append({
        "properties": {
            "name": file,
            "version": "0.x.x",
            "service": "misc",
            "exclusive": "no",
            },
        "order": {
            "before": "[]",
            "after": "[]",
            }
        })

    # Update with actual values
    if "properties" in plugin:
        plugins[-1]["properties"].update(plugin["properties"])
    if "order" in plugin:
        plugins[-1]["order"].update(plugin["order"])

    try:
        importlib.import_module(plugin["properties"]["name"]+".precheck")
    except ModuleNotFoundError:
        pass
    except Exception as e:
        log("Problem running precheck for " + plugin["properties"]["name"])
        raise e

    # Process json
    plugins[-1]["order"]["before"] = json.loads(plugins[-1]["order"]["before"])
    plugins[-1]["order"]["after"] = json.loads(plugins[-1]["order"]["after"])


def log(string, level=3, end="\n"):
    if level <= LOGLEVEL:
        print(string, end=end)


# =============================================================================
#   Prepare Environment
# =============================================================================
os.chdir(sys.path[0])  # Set program directory
pluginFileExtensions = {
    ".jpp": loadAPM,  # .jpp - JukePi Plugin (DEPRECATED)
    ".apm": loadAPM,  # .apm - APPLES Plugin Manifest
    }


# =============================================================================
#   Read Module Info
# =============================================================================
log("Identifying plugins...", end=" ")
plugins = []
for file in os.listdir(sys.path[0]):
    if os.path.isfile(os.path.join(sys.path[0], file)):
        for extension in pluginFileExtensions.keys():
            if file[-1*len(extension):].lower() == extension.lower():
                pluginFileExtensions[extension](file)
log("done!")


# =============================================================================
#   Order Plugins
# =============================================================================
log("Ordering plugins...", end=" ")
unsorted = True
while unsorted:
    original = []
    for plugin in plugins:
        for target in plugin["order"]["after"]:
            if target["plugin"] == "^ALL":
                for p in plugins:
                    if p != plugin:
                        plugin["order"]["after"].append({
                            "plugin": p["properties"]["name"],
                            "priority": target["priority"]})
            del target
        original.append(plugin["properties"]["name"])

    for plugin in range(0, len(plugins)):
        for target in plugins[plugin]["order"]["after"]:
            if target["plugin"][0] == "$":
                last = 0
                for item in range(0, len(plugins)):
                    if plugins[item]["properties"]["service"] == \
                            target["plugin"][1:] and item > plugin:
                        plugins.insert(item + 1, plugins.pop(plugin))
                        break
            else:
                last = 0
                for item in range(0, len(plugins)):
                    if plugins[item]["properties"]["name"] == \
                            target["plugin"][0:] and item > plugin:
                        plugins.insert(item + 1, plugins.pop(plugin))
                        break

    unsorted = False
    for plugin in range(0, len(plugins)):
        if original[plugin] != plugins[plugin]["properties"]["name"]:
            unsorted = True
log("done!")


# =============================================================================
#   Load Plugins
# =============================================================================
modules = []
for plugin in plugins:
    log("Loading " + plugin["properties"]["name"] + "...", end=" ")
    modules.append(importlib.import_module(plugin["properties"]["name"]))
    log("done!")


# =============================================================================
#   Create Service List
# =============================================================================
log("Creating list of services...", end=" ")
services = {}
services["*"] = []
for plugin in range(0, len(plugins)):
    services[plugins[plugin]["properties"]["service"]] = \
        services.get(
            plugins[plugin]["properties"]["service"], []) + [modules[plugin]]
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
