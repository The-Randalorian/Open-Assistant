import os  # Library used for acessing basic os features
import sys  # Library used for acessing core system features
# import importlib        #Library used for dynamically loading libriaries
import configparser  # Library used for reading library information
import json  # Library used for reading load order information
# import traceback        #Library used for getting error information
import urllib.request  # Library used for downloading files
# import concurrent.futures



def loadAPM(file):
    '''
Loads and processes APM files into usable forms
'''
    # Perform initial read
    plugin = configparser.ConfigParser()
    plugin.read_string(file.read().decode())

    # Convert to dictionary
    plugin = dict(plugin.items())
    for i, j in plugin.items():
        plugin[i] = dict(j.items())

    # Create dictionary with default values
    plugin_data = {
        "properties": {
            "name": file,
            "version": "0.x.x",
            "service": "misc",
            "exclusive": "no",
        },
        "updates": {
            "format": "0.0.0",
            "remoteroot": None,
            "localroot": None,
            "files": "[]",
        },
    }

    # Update with actual values
    if "properties" in plugin:
        plugin_data["properties"].update(plugin["properties"])
    if "updates" in plugin:
        plugin_data["updates"].update(plugin["updates"])

    # Replace local directories
    if plugin_data["updates"]["localroot"] != None:
        for key in pathReplacements.keys():
            plugin_data["updates"]["localroot"] = plugin_data["updates"]["localroot"].replace(key,
                                                                                              pathReplacements[key])

    # Process json
    plugin_data["updates"]["files"] = json.loads(plugin_data["updates"]["files"])
    return plugin_data

def check_for_new_manifest(plugin):
    for file_name in plugin["updates"]["files"]:
        if file_name.split(".")[-1] == "apm":
            with urllib.request.urlopen(get_remote_url(plugin, file_name)) as remote_manifest:
                remote_plugin = loadAPM(remote_manifest)
                if remote_plugin["properties"]["version"] != plugin["properties"]["version"]:
                    return True, remote_plugin
    return False, plugin



def get_remote_url(plugin, file_name):
    return plugin["updates"]["remoteroot"] + file_name


def get_local_url(plugin, file_name):
    return plugin["updates"]["localroot"] + file_name


pathReplacements = {
    "_APPLES_": sys.path[0],
    }

def download(plugin):
    remotes = []
    locals = []
    for file_name in plugin["updates"]["files"]:
        remotes.append(get_remote_url(plugin, file_name))
        locals.append(get_local_url(plugin, file_name))

    print(remotes, locals)

    for local, remote in zip(locals, remotes):
        print(local, remote)
        urllib.request.urlretrieve(remote, local)


def verify(plugin):
    for file_name in plugin["updates"]["files"]:
        local = get_local_url(plugin, file_name)
        print(local)
        if not os.path.isfile(local):
            return False
    return True

def update_plugin(plugin):
    print(plugin)
    updated, plugin = check_for_new_manifest(plugin)
    print(plugin)
    if updated or not verify(plugin):
        download(plugin)