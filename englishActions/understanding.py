#!/usr/bin/env python3
'''
This file contains the "Thing" object, the main concept behind how
OpenAssistant handles interpreting sentences into meaning. Things are objects
with many various semi-standardized interfaces for interaction from other
scripts and Things. A Thing (or a Thing subclass!) instance represents an
actual object or concept in the real world. As sentences are unpacked by
speech.py, the (ideally) correct Thing instances are collected for
interpretation by code. If an instruction is given to do something, one of the
instances' Actions (Action is a class used to add metadata to functions) are
called with a verb parameter so the object can further interpret what was
intended.
'''

def _placeholder_function(*args, **kwargs):
    return

class Thing():
    things = {}
    thing_types = {}
    _thing_type_placeholder = _placeholder_function
    classifications = []

    def __init__(self, **kwargs):
        self.name = kwargs.pop("name")
        Thing.things[self.name] = self
        self.actions = {}
        self.any_actions = {}
        super().__init__(**kwargs)

    @classmethod
    def __init_subclass__(cls, **kwargs):
        cls.classifications = list(getattr(super(cls, cls), "classifications", []))
        cls.classifications.append(Thing._thing_type_placeholder(cls))
        super().__init_subclass__(**kwargs)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    @classmethod
    def get_by_name(cls, name, **kwargs):
        return ThingReference(name)

    def perform_action(self, verb):
        #print(self.any_actions)
        #print(self.actions)
        if verb.text in self.any_actions.keys():
            response = self.any_actions[verb.text](verb)
            return response
        objs = verb.obj
        # print(self.actions)
        if len(objs) <= 0:
            objects = [self]
        else:
            objects = []
            for obj in objs:
                objects.append(obj.thing)
        response = ""
        for object in objects:
            if object in self.actions.keys():
                oa = self.actions[object]
                if verb.lemma in oa.keys():
                    response += oa[verb.text](verb)
                else:
                    print(f"No {verb.lemma} action for {object}")
            else:
                print(f"No actions for {object}")
        self.update_pronouns()
        return response

    def add_action(self, action):
        if action.any:
            self.any_actions[action.root] = action
        else:
            self.actions.setdefault(action.thing, {})[action.root] = action

    def make_action(self, function, root, thing, any=False):
        self.add_action(Action(function, root, thing, any))

    def get_ref(self, *args, **kwargs):
        return self

    def get_classifications(self):
        yield from self.classifications

    def classify(self, classification):
        response = "Ok."
        if isinstance(classification, str):
            classification = Thing.thing_types[classification]
        Thing.things[self.name] = classification(**self.__dict__)
        Thing.things[self.name].update_pronouns()
        #print(Thing.things[self.name])
        return response

    @classmethod
    def is_one(cls, instance):
        while isinstance(instance, ThingReference):
            instance = instance.get_ref()
        return isinstance(instance, cls)

    def update_pronouns(self):
        Thing.things["it"] = ThingReference(self.name)


def ClearPronouns():
    for pron in ["they", "it", "he", "she"]:
        Thing.things.pop(pron, None)


class ThingType(Thing):
    """Thing that acts as a reference to a thing class. These are created
    automatically using the class name as the the name of the ThingType.
    Custom Thing Types can also be created, and can use custom constructor
    and comparison methods to make and check classifications."""
    def __init__(self, thing_class, **kwargs):
        kwargs.setdefault("name", thing_class.__name__.lower())
        self.thing_class = thing_class
        self.constructor = kwargs.pop("constructor", thing_class)
        self.comparison = kwargs.pop("comparison", thing_class.is_one)
        Thing.thing_types[kwargs["name"]] = self.constructor
        super().__init__(**kwargs)

    def check_is_one(self, instance):
        return self.comparison(instance)

    def ask_is_one(self, instance):
        if self.check_is_one(instance):
            return getattr(instance, "called", instance.name) + " is a " + getattr(self, "called", "name") + "."
        else:
            return getattr(instance, "called", instance.name) + " is not a " + getattr(self, "called", "name") + "."

Thing._thing_type_placeholder = ThingType

class ThingReference(Thing):
    """Transparent reference to a thing, will be updated if an object is
    replaced. If at all possible, use this to reference objects, as it will
    ensure changes are kept properly. This object should act EXACTLY like its
    referenced Thing, however in the event that it doesn't, the get_ref
    function will return the exact object. Be aware this returned reference
    will no longer update automatically, so it should be used immediately and
    should not be stored.

    This class basically just redirects all function calls to the Thing it
    points to. This includes several 'magic' methods, making this object work
    even as a dictionary key."""

    def __init__(self, name):
        self.__dict__["name"] = name

    def __str__(self):
        return str(self.get_ref())

    def __repr__(self):
        return repr(self.get_ref())

    def __getattr__(self, attribute):
        return getattr(self.get_ref(), attribute)

    def __setattr__(self, attribute, value):
        setattr(self.get_ref(), attribute, value)

    def __hash__(self):
        return hash(self.get_ref())

    def __eq__(self, other):
        return self.get_ref() == other

    def __ne__(self, other):
        return self.get_ref() != other

    def __lt__(self, other):
        return self.get_ref() < other

    def __gt__(self, other):
        return self.get_ref() > other

    def __le__(self, other):
        return self.get_ref() <= other

    def __ge__(self, other):
        return self.get_ref() >= other

    def __dir__(self):
        return dir(self.get_ref())

    def perform_action(self, *args, **kwargs):
        val = self.get_ref().perform_action(*args, **kwargs)

        return val

    def add_action(self, *args, **kwargs):
        return self.get_ref().add_action(*args, **kwargs)

    def make_action(self, *args, **kwargs):
        return self.get_ref().make_action(*args, **kwargs)

    def get_ref(self, *args, **kwargs):
        thing = Thing.things.get(self.name, None)
        if thing is None:
            thing = Thing(name=self.name)
        return thing.get_ref(*args, **kwargs)

    def get_classifications(self):
        yield from self.get_ref().get_classifications()

    @property
    def classifications(self):
        return self.get_ref().classifications


class Action():
    def __init__(self, function, root, thing, any=False):
        self.function = function
        self.root = root
        self.thing = thing
        self.any = any

    def __call__(self, verb):
        return self.function(verb)
