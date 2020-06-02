class Thing():
    things = {}

    def __init__(self, **kwargs):
        self.name = kwargs.pop("name")
        Thing.things[self.name] = self
        self.actions = {}
        self.any_actions = {}
        super().__init__(**kwargs)

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
                if verb.text in oa.keys():
                    response += oa[verb.text](verb)
                else:
                    print(f"No {verb.text} action for {object}")
            else:
                print(f"No actions for {object}")
        return response

    def add_action(self, action):
        if action.any:
            self.any_actions[action.root] = action
        else:
            self.actions.setdefault(action.thing, {})[action.root] = action

    def make_action(self, function, root, thing, any=False):
        self.add_action(Action(function, root, thing, any))

    def get_ref(self):
        return self


class ThingReference(Thing):
    '''Transparent reference to a thing, will be updated if an object is
    replaced. If at all possible, use this to reference objects, as it will
    ensure changes are kept properly. This object should act EXACTLY like it's
    referenced Thing, however in the event that it doesn't, the get_ref
    function will return the exact object. Be aware this returned reference
    will no longer update automatically, so it should be used immediately and
    should not be stored.

    This class basically just redirects all function calls to the Thing it
    points to. This includes several 'magic' methods, making this object work
    even as a dictionary key.'''

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
        return self.get_ref().perform_action(*args, **kwargs)

    def add_action(self, *args, **kwargs):
        return self.get_ref().add_action(*args, **kwargs)

    def make_action(self, *args, **kwargs):
        return self.get_ref().make_action(*args, **kwargs)

    def get_ref(self, *args, **kwargs):
        thing = Thing.things.get(self.name, None)
        if thing is None:
            thing = Thing(name=self.name)
        return thing.get_ref(*args, **kwargs)


class Action():
    def __init__(self, function, root, thing, any=False):
        self.function = function
        self.root = root
        self.thing = thing
        self.any = any

    def __call__(self, verb):
        return self.function(verb)
