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
    plugins.append({
        "properties": {
            "name"      : file,
            "version"   : "0.x.x",
            "service"   : "misc",
            "exclusive" : "no",
            },
        "updates"   : {
            "remoteroot": None,
            "localroot" : None,
            "files"     : "[]",
            },
        })

    #Update with actual values
    if "properties" in plugin:
        plugins[-1]["properties"].update(plugin["properties"])
    if "updates" in plugin:
        plugins[-1]["updates"].update(plugin["updates"])

    #Replace local directories
    if plugins[-1]["updates"]["localroot"] != None:
        for key in pathReplecements.keys():
            plugins[-1]["updates"]["localroot"] = plugins[-1]["updates"]["localroot"].replace(key, pathReplecements[key])
        
    #Process json
    plugins[-1]["updates"]["files"] = json.loads(plugins[-1]["updates"]["files"])

def log(string, level=3, end="\n"):
    if level <= LOGLEVEL:
        print("[updater]: " + string, end = end)

def findManifest(plugin):
    fileNum = None
    files = plugin["updates"]["files"]
    for file in range(0, len(files)):
        for extension in pluginFileExtensions.keys():
            if files[file][0][-len(extension):].lower() == extension.lower() or files[file][1][-len(extension):].lower() == extension.lower():
                fileNum = file
                break
        if fileNum != None:
            break
    return fileNum

def createURLs(local, remote, files):
    f = []

    #fix paths with trailing slashes
    if local[-1] == os.sep or local[-1] == "\\" or local[-1] == "/":
        local = local[:-1]
    if remote[-1] == os.sep or remote[-1] == "\\" or remote[-1] == "/":
        remote = remote[:-1]
    
    for file in files:
        f.append([])
        f[-1].append(local + os.sep + file[0])
        f[-1].append(remote + "/" + file[1])
        
    return f

def update(local, remote):
    log("updating " + local["properties"]["name"])
    localURLs = createURLs(local["updates"]["localroot"], local["updates"]["remoteroot"], local["updates"]["files"])
    remoteURLs = createURLs(remote["updates"]["localroot"], remote["updates"]["remoteroot"], remote["updates"]["files"])

    #Not sure how to handle local files. Should they be purged? Kept?
    #Right now if you want them removed your program must do it itself.
    #Also prechecks need to be identified, so this script isn't overwritten
    #while it is currently running. It shouldn't matter because it should
    #just be loaded into memory, but better safe than sorry.

    for urlSet in remoteURLs:
        urllib.request.urlretrieve(urlSet[1], urlSet[0])
    

#===============================================================================
#   Prepare Environment
#===============================================================================
#os.chdir(sys.path[0]) #Set program directory
pluginFileExtensions = {
    ".jpp": loadAPM, #.jpp - JukePi Plugin (DEPRECATED)
    ".apm": loadAPM, #.apm - APPLES Plugin Manifest
    }
pathReplecements = {
    "_APPLES_": sys.path[0],
    }

#===============================================================================
#   Read Module Info
#===============================================================================
log("Identifying plugins to update...", end = " ")
plugins = []
for file in os.listdir(sys.path[0]):
    if os.path.isfile(os.path.join(sys.path[0], file)):
        for extension in pluginFileExtensions.keys():
            if file[-1*len(extension):].lower() == extension.lower():
                pluginFileExtensions[extension](file)

for plugin in plugins:
    if plugin["updates"]["localroot"] != None and plugin["updates"]["remoteroot"] != None:
        urls = createURLs(plugin["updates"]["localroot"], plugin["updates"]["remoteroot"], plugin["updates"]["files"])
        man = findManifest(plugin)


        remoteManifest = configparser.ConfigParser()
        localVer = plugin["properties"]["version"].split(".")
        for num in range(0, len(localVer)):
            localVer[num] = int(localVer[num])

        with urllib.request.urlopen(urls[man][1]) as response:
            remoteManifest.read_string(response.read().decode())
            remoteVer = remoteManifest["properties"]["version"].split(".")
            if len(remoteVer) != len(localVer):
                update(localManifest, remoteManifest)
            else:
                for num in range(0, len(remoteVer)):
                    if int(remoteVer[num]) == localVer[num]:
                        continue
                    elif int(remoteVer[num]) < localVer[num]:
                        break
                    else:
                        remoteManifest = dict(remoteManifest.items())
                        for i, j in remoteManifest.items():
                            remoteManifest[i] = dict(j.items())
                        if remoteManifest["updates"]["localroot"] != None:
                            for key in pathReplecements.keys():
                                remoteManifest["updates"]["localroot"] = remoteManifest["updates"]["localroot"].replace(key, pathReplecements[key])
                        remoteManifest["updates"]["files"] = json.loads(remoteManifest["updates"]["files"])
                        update(plugin, remoteManifest)
                
            
     
