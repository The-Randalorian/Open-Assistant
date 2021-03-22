#!/usr/bin/env python3

import logging
import yeelight
import json

from ... import plugins

core = plugins.services["core"][0]
actions = plugins.services["actions"][0]
terminal = plugins.services["terminal"][0]
ha = plugins.services["home_automation"][0]

_logger = logging.getLogger(f"{__name__}")


lights = []
light_data = []


class YeelightSmartLight(ha.AutomationSmartLightColor):
    def __init__(self, ip, new_light=True, **kwargs):
        global lights
        super().__init__(**kwargs)
        self.ip = ip
        self.light = len(lights)
        lights.append(yeelight.Bulb(self.ip))
        lights[self.light].auto_on = True
        if new_light:
            light_data.append({"ip": self.ip, "name": self.name})
        with open(__file__[:-11] + "lights.json", "w") as f:
            json.dump(light_data, f)

    def toggle_on(self):
        global lights
        _logger.info("Turning on ")
        lights[self.light].turn_on()
        return "Okay"

    def toggle_off(self):
        global lights
        lights[self.light].turn_off()
        return "Okay"

    def set_color(self, color):
        global lights
        col = [int(b*255) for b in color]  # super().setColor(root, raw = True)
        lights[self.light].set_rgb(col[0], col[1], col[2])
        return "Okay"


try:
    with open(__file__[:-11] + "lights.json", "r") as f:
        light_data = json.load(f)
    for ld in light_data:
        YeelightSmartLight(ld["ip"], new_light=False, name=ld["name"])
except FileNotFoundError:
    pass


def textConnect(arguments):
    """
INFO
    Setup a connection to a new yeelight

USAGE
    {0}
    """
    print("Discovering Lights")
    lightData = yeelight.discover_bulbs()
    if len(lightData) > 0:
        for i in range(len(lightData)):
            print(str(i + 1) + ". ", end="")
            if lightData[i]["capabilities"]["name"] == "":
                print("Unnamed Light")
            else:
                print(lightData[i]["capabilities"]["name"])
        try:
            n = int(input("enter a light number to connect to. ")) - 1
            name = input("what would you like to call it. (recommended: lights) ").lower()
            if n < len(lightData):
                YeelightSmartLight(lightData[i]["ip"], name=name)
        except ValueError as e:
            print("invalid input")
    else:
        print("No lights detected! Make sure they are on and connected to the same network.")
