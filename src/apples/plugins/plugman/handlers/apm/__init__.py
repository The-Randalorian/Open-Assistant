import urllib.request
import json

from . import f0_1_0


_apm_json_handlers = {
    "0.1.0": f0_1_0
}


def install(plugin_remote_url, repository):
    print(f"getting {plugin_remote_url}")
    with urllib.request.urlopen(plugin_remote_url) as plugin_manifest_file:
        plugin_manifest = json.load(plugin_manifest_file)
        _apm_json_handlers[plugin_manifest["format"]].install(plugin_manifest, plugin_manifest_file, plugin_remote_url, repository)
