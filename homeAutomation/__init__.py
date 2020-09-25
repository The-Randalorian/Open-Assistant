import threading, time, re


services = {}
plugin = {}
core = None
actions = None
understanding = None
speech = None
general_knowledge = None
Thing = None
runThread = None
threadActive = False
num_pat = re.compile(r"(-?)((\d+)\.(\d*))")


def _register_(serviceList, pluginProperties):
    global services, plugin, core, actions
    global understanding, speech, general_knowledge, Thing
    services = serviceList
    plugin = pluginProperties
    core = services["core"][0]
    actions = services["actions"][0]
    understanding = actions.understanding
    speech = actions.speech
    general_knowledge = actions.general_knowledge
    Thing = understanding.Thing
    _make_classes()
    #light = AutomationSmartLightColor(name="light")


def _make_classes():
    _make_automation_interface()
    _make_automation_toggle()
    _make_automation_scalar()
    _make_automation_smart_light_white()
    _make_automation_smart_light_color()


def _make_automation_interface():
    global AutomationInterface

    class AutomationInterface(Thing):
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


def _make_automation_toggle():
    global AutomationToggle

    class AutomationToggle(AutomationInterface):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.add_action_to_system(
                self._toggle_action,
                ("toggle", "turn", "switch")
            )

        def _toggle_action(self, verb):
            '''Toggle action. Turns speech parts into usable data.'''
            for advmod in verb.advmod:
                if advmod == "on":
                    return self.toggleOn()
                elif advmod == "off":
                    return self.toggleOff()

        def toggleOn(self):
            print("Default AutomationToggle turnOn function.")
            return "Default AutomationToggle turnOn function."

        def toggleOff(self):
            print("Default AutomationToggle turnOff function.")
            return "Default AutomationToggle turnOff function."


def _make_automation_scalar():
    global AutomationScalar

    class AutomationScalar(AutomationInterface):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.add_action_to_system(
                self._set_action,
                ("set",)
            )

        def _set_action(self, verb):
            '''Set action. Turns speech parts into usable data.'''
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

        def setLevel(self, level):
            print("Default AutomationScalar setLevel function.")
            print(f"level = {level}")
            s = "Default AutomationScalar setLevel function."
            s += f" Level set to {level}."
            return s


def _make_automation_smart_light_white():
    global AutomationSmartLightWhite

    class AutomationSmartLightWhite(AutomationScalar, AutomationToggle):
        def __init__(self, level_aliases=("level", "brightness"), **kwargs):
            super().__init__(**kwargs)
            self.add_action_to_system(
                self._set_action,
                ("dim", "brighten", "darken")
            )


def _make_automation_smart_light_color():
    global AutomationSmartLightColor

    class AutomationSmartLightColor(AutomationSmartLightWhite):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.add_action_to_system(
                self._set_color_action,
                ("set", "make")
            )

        def _set_color_action(self, verb):
            '''Set action for color. Turns speech parts into usable data. if it
            doesn't find a color, it will run a regular set'''
            for obl in verb.obl:
                if obl.text in general_knowledge.Color.colors.keys():
                    return self.setColor(obl.thing.get_color())
            return self._set_action(verb)  # Run regular set if no color stated

        def setColor(self, color):
            print("Default AutomationSmartLightColor setColor function.")
            print(f"color = {color}")
            s = "Default AutomationSmartLightColor setColor function."
            s += f" Color set to {color}."
            return s
