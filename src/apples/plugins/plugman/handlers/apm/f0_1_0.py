import urllib.request
import shutil
import os


from ..... import plugins

APPLE_DIRECTORY = plugins.APPLE_DIRECTORY
PLUGIN_DIRECTORY = plugins.PLUGIN_DIRECTORY


def install(plugin_manifest, plugin_manifest_file, plugin_remote_url, repository):
    install_files(plugin_manifest)


def install_files(plugin_manifest):
    for file in plugin_manifest["files"]:
        local_url = os.path.join(APPLE_DIRECTORY, file["local-url"])
        remote_url = file["remote-url"]
        try:
            os.makedirs(os.path.dirname(local_url))
        except FileExistsError:
            pass
        print(remote_url, local_url)
        urllib.request.urlretrieve(remote_url, local_url)
