#!/usr/bin/env python3

import logging
import re

from ... import plugins

core = plugins.services["core"][0]
actions = plugins.services["actions"][0]
understanding = actions.understanding
speech = actions.speech
general_knowledge = actions.general_knowledge

_logger = logging.getLogger(f"{__name__}")

num_pat = re.compile(r"(-?)((\d+)\.(\d*))")


class AutomationInterface(understanding.Thing):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def add_action_to_system(self, function, roots):
        for root in roots:
            action = understanding.Action(
                function=function,
                root=root,
                thing=self
            )
            general_knowledge.SystemPersonality.add_system_action(action)


class AutomationToggle(AutomationInterface):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_action_to_system(
            self._toggle_action,
            ("toggle", "turn", "switch")
        )

    def _toggle_action(self, verb):
        '''
        Toggle action. Turns speech parts into usable data.
        '''
        for advmod in verb.advmod:
            if advmod == "on":
                return self.toggleOn()
            elif advmod == "off":
                return self.toggleOff()

    def toggle_on(self):
        print("Default AutomationToggle turnOn function.")
        return "Default AutomationToggle turnOn function."

    def toggle_off(self):
        print("Default AutomationToggle turnOff function.")
        return "Default AutomationToggle turnOff function."


class AutomationScalar(AutomationInterface):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_action_to_system(
            self._set_action,
            ("set",)
        )

    def _set_action(self, verb):
        '''
        Set action. Turns speech parts into usable data.
        '''
        for obl in verb.obl:
            raw_num = re.match(num_pat, obl.text)
            if raw_num is None:
                if len(obl.nummods) <= 0:
                    continue
                raw_num = re.match(num_pat, obl.nummods[0].text)
            num = int(raw_num.group(0))
            if obl.text == "percent":
                num = num/100.0
            return self.setLevel()
        return "Sorry, I didn't catch that."

    def set_level(self, level):
        print("Default AutomationScalar setLevel function.")
        print(f"level = {level}")
        s = "Default AutomationScalar setLevel function."
        s += f" Level set to {level}."
        return s


class AutomationSmartLightWhite(AutomationScalar, AutomationToggle):
    def __init__(self, level_aliases=("level", "brightness"), **kwargs):
        super().__init__(**kwargs)
        self.add_action_to_system(
            self._set_action,
            ("dim", "brighten", "darken")
        )


class AutomationSmartThermostat(AutomationScalar, AutomationToggle):
    def __init__(self, level_aliases=("level", "brightness"), **kwargs):
        super().__init__(**kwargs)
        self.add_action_to_system(
            self._set_action,
            ("dim", "brighten", "darken")
        )


class AutomationSmartLightColor(AutomationSmartLightWhite):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_action_to_system(
            self._set_color_action,
            ("set", "make")
        )

    def _set_color_action(self, verb):
        """
        Set action for color. Turns speech parts into usable data. if it
        doesn't find a color, it will run a regular set
        """
        for obl in verb.obl:
            if obl.text in general_knowledge.Color.colors.keys():
                return self.setColor(obl.thing.get_color())
        return self._set_action(verb)  # Run regular set if no color stated

    def set_color(self, color):
        print("Default AutomationSmartLightColor setColor function.")
        print(f"color = {color}")
        s = "Default AutomationSmartLightColor setColor function."
        s += f" Color set to {color}."
        return s
