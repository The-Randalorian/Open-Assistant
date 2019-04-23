import englishActions as actions
import pickle
import time
import datetime

memformat = "0.2.0"

class Thing:
    def __init__(self, w=True, d="", t="string", a={}):
        self.writeable = w
        self.setData(d=d, t=t)
        self.settime = time.time()
        self.attributes = a

    def __str__(self):
        return str(self.getData()) + str(self.attributes)

    def __repr__(self):
        return repr(self.getData()) + repr(self.attributes)

    def setData(self, d="", t=None):
        if t == None:
            if isinstance(d, str):
                t = "string"
            elif d == None:
                t = "idea"
        self.dataType = t
        self.dataValue = d

    def getData(self):
        if self.dataType == "string":
            return self.dataValue
        elif self.dataType == "idea":
            return None
        elif self.dataType == "functional":
            return self.dataValue()
    def get(self, key, value):
        return self.attributes.get(key, value)

    def __getitem__(self, key):
        return self.attributes[key]

    def __setitem__(self, key, value):
        self.attributes[key] = value
    
    def getRef(self):
        return self

class link:
    links = []
    def __init__(self, path=""):
        self.path = path
        link.links.append(self)
        self.ref = None

    def __str__(self):
        return str(self.ref)

    def __repr__(self):
        return "<" + self.path + "> "

    @classmethod
    def setLinks(cls):
        for self in cls.links:
            self.linkTo()

    @property
    def writeable(self):
        return self.ref.writeable

    @writeable.setter
    def writeable(self, w):
        self.ref.writeable = w

    def linkTo(self):
        global mem
        path = self.path.split(".")
        if isinstance(path, str):
            path = [path]
        placement = mem
        for l in path:
            placement = placement[l]
        self.ref = placement
        

    def setData(self, d="", t=None):
        return self.ref.setData(d, t)

    def getData(self):
        return self.ref.getData()

    def get(self, key, value):
        return self.ref.get(key, value)

    def __getitem__(self, key):
        return self.ref[key]

    def getRef(self):
        return self

def data_getTime():
    return str(datetime.datetime.now().strftime("%I:%M %p"))

mem = {
    "green": Thing(w=False, d="green", t="string", a={
        }),
    "red": Thing(w=False, d="green", t="string", a={
        }),
    "blue": Thing(w=False, d="green", t="string", a={
        }),
    "yellow": Thing(w=False, d="green", t="string", a={
        }),
    "orange": Thing(w=False, d="green", t="string", a={
        }),
    "purple": Thing(w=False, d="green", t="string", a={
        }),
    "pink": Thing(w=False, d="green", t="string", a={
        }),
    "color": Thing(w=False, d=None, t="idea", a={
        "best": link("green"),
        }),
    "time": Thing(w=False, d=data_getTime, t="functional", a={
        }),
    "^USER": Thing(w=False, d=None, t="idea", a={ #I, me, mine
        }),
    "^MALE": Thing(w=False, d=None, t="idea", a={ #He, him, his
        }),
    "^FMAL": Thing(w=False, d=None, t="idea", a={ #She, her, hers
        }),
    }

link.setLinks()

memHeads = {
    "poss":{
        "I":"^USER",
        "me":"^USER",
        "my":"^USER",
        "mine":"^USER",
        "he":"^MALE",
        "him":"^MALE",
        "his":"^MALE",
        "she":"^FMAL",
        "her":"^FMAL",
        "hers":"^FMAL",
        },
    }
memChildsPath = {
    "acomp": None,
    "attr": None,
    "amod":{
        "advmod": None,
        }
    }

def _close():
    global mem
    with open('englishActions/vbf.oam', mode="wb") as f:
        pickle.dump({"format": memformat, "memory": mem}, f)

def _open():
    global mem
    try:
        with open('englishActions/vbf.oam', mode="rb") as f:
            rawdat = pickle.load(f)
            if rawdat["format"] == memformat:
                mem = rawdat["memory"]
    except EOFError:
        pass
    except FileNotFoundError:
        pass

def vb_be(root, subjects):
    global mem
    ret = ""
    interrogative = False
    for subject in subjects:
        for s in subject:
            if s.tag_[0] == u'W':
                interrogative = True
                break
    if not interrogative:
        attributes = actions.getDependency(root, u'attr')
        for attr in attributes:
            if attr.tag_[0] == u'W':
                interrogative = True
                break
            for det in actions.getDependency(attr, u'det'):
                if det.tag_[0] == u'W':
                    interrogative = True
                    break
    if interrogative:
        for subject in subjects:
            for s in subject:
                if s.text != "what":
                    item = [s.text]
                    for head in memHeads.keys():
                        for h in actions.getDependency(s, head):
                            item.insert(0, memHeads[head].get(h.text, h.text))
                    vb_be_childsearch(memChildsPath, item, s)
                    path = mem
                    for part in item:
                        p = path.get(part, Thing(d = None, t = "idea"))
                        path[part] = p
                        path = p
                    if path.getData() == None:
                        ret += "I don't know. "
                    else:
                        ret += path.getData()
    else:
        for subject in subjects:
            for s in subject:
                item = [s.text]
                for head in memHeads.keys():
                    for h in actions.getDependency(s, head):
                        item.insert(0, memHeads[head].get(h.text, h.text))
                vb_be_childsearch(memChildsPath, item, s)
                path = mem
                for part in item:
                    p = path.get(part, Thing(d = None, t = "idea"))
                    path[part] = p
                    path = p
                deps = ["acomp", "attr"]
                for dep in deps:
                    val = actions.getDependency(root, dep)
                    if len(val) > 0:
                        if path.writeable:
                            path.setData(val[0].text)
                            ret += "okay. "
                        else:
                            if val[0].text != path.getData():
                                ret += "No, it's not. "
                            else:
                                ret += "Yes, it is. "
    return ret

def vb_be_childsearch(p, item, s):
    for child in p.keys():
        for c in actions.getDependency(s, child):
            item.append(c.text)
            if p[child] != None:
                vb_be_childsearch(p[child], item, c)
    #return item
    
vbz = {
    "be":vb_be
    }
