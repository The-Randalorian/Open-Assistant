
'''
This contains classes and information used to create a general knowledge base
for open assistant. It does not contain every type of object, however it
contains many types of objects that are important for many things, such as
times. It also contains certain abstract things, such as colors.

The purpose is to provide a basic "understanding" of common objects,
particularly ones useful for a voice assistant.

What's important to note is that these classes are just that; classes. They
should cover a general type of object, such as a color, song, or time, and give
meaning to its attributes in a way that would be useful to other plugins. For
example, the color class has a "color" attribute and several other functions.
These are useful for associating color names with an actual RGB color, making
lightbulbs and other devices. There may be a few specialized classes, like
"Now", but those should only be used for specific functionality.

Also important to note is that these objects are, at their core,
understanding.Things. Certain objects with no real programatic meaning, such as
a "ball" won't be defined here because there is little to no use for
understanding what a "ball" is. A "ball" would therefore just be an instance of
understanding.Thing.
'''


import colorsys
import json
from datetime import datetime
import dateutil.tz
from collections import namedtuple

try:
    from .understanding import Thing, Action
except ImportError:
    from understanding import Thing, Action

general_knowledge = {}


class Color(Thing):
    colors = {}

    def __init__(self, **kwargs):
        color = kwargs.pop("color", (1.0, 1.0, 1.0))
        if color[0] == "#":
            color = Color.hex_to_rgb(color)
        self.color = color
        super().__init__(**kwargs)
        Color.colors[self.name] = self

    @staticmethod
    def hex_to_rgb(value):
        value = value.lstrip('#')
        lv = len(value)
        cs = lv // 3
        ns = 2 ** (cs * 4) - 1
        return tuple(int(value[i:i + cs], 16) / ns for i in range(0, lv, cs))

    def get_color(self, color_system="rgb"):
        if color_system == "rgb":
            return self.get_rgb()
        elif color_system == "yiq":
            return self.get_yiq()
        elif color_system == "hls":
            return self.get_hls()
        elif color_system == "hsv":
            return self.get_hsv()
        else:
            raise ValueError(color_system)

    def get_rgb(self):
        return self.color

    def get_yiq(self):
        return colorsys.rgb_to_yiq(*self.color)

    def get_hls(self):
        return colorsys.rgb_to_hls(*self.color)

    def get_hsv(self):
        return colorsys.rgb_to_hsv(*self.color)

    def __str__(self):
        return f"{self.name}: {repr(self.get_rgb())}"

    def __repr__(self):
        return str(self)


class DateTime(Thing):
    _utc, _local = dateutil.tz.tzutc(), dateutil.tz.tzlocal()

    def __init__(self, **kwargs):
        time = kwargs.pop("time", datetime.now())
        self.timezone = kwargs.pop("timezone", DateTime._local)
        if time.tzinfo is None or time.tzinfo.utcoffset(time) is None:
            self.time = time.astimezone(DateTime._utc)
        else:
            self.time = time
        super().__init__(**kwargs)

    @classmethod
    def from_datetime_string(cls, datetime_str, timezone=_local,
                             format='%m/%d/%Y %H:%M:%S', **kwargs):
        time = datetime.strptime(datetime_str, format)
        return cls(time=time, timezone=timezone, **kwargs)

    def __str__(self):
        t = self.time.astimezone(self.timezone)
        return t.strftime('%m/%d/%Y %H:%M:%S')


class Now(DateTime):
    def __set_time(self, value):
        pass

    def __get_time(self):
        return datetime.now().datetime.now()

    time = property(__get_time, __set_time)


'''
class Book(Thing):
    def __init__(self, **kwargs):
        self.title = kwargs.pop("title", "No Title")
        self.authors = kwargs.pop("authors", ("Unknown"))
        self.publisher = kwargs.pop("publisher", "Unknown")
        self.genres = kwargs.pop("genres", ("Unknown"))
        self.date = kwargs.pop("date", None)
        super().__init__(**kwargs)


class Song(Thing):
    def __init__(self, **kwargs):
        self.title = kwargs.pop("title", "No Title")
        self.artists = kwargs.pop("artists", ("Unknown"))
        self.album = kwargs.pop("album", "Unknown")
        self.genres = kwargs.pop("genres", ("Unknown"))
        self.date = kwargs.pop("date", None)
        super().__init__(**kwargs)
'''

Relation = namedtuple("Relation", "person method")


class Person(Thing):
    people = {}
    opinion_ratings = {
        "like": 1,
        "love": 2,
        "dislike": -1,
        "hate": -2
    }

    def __init__(self, **kwargs):
        self.gender = kwargs.pop("gender", "Unknown")
        self.birthday = kwargs.pop("birthday", None)
        self.relations = kwargs.pop("relations", [])
        self.called = kwargs.pop("called", None)
        self.tense = kwargs.pop("tense", "s")
        self.opinions = {}
        for opinion, rating in kwargs.pop("opinions", []):
            self.opinions[opinion] = [rating]
        super().__init__(**kwargs)
        if self.called is None:
            self.called = self.name
        Person.people[self.name] = self
        self.make_action(self._like_action, "like", self, True)
        self.make_action(self._like_action, "love", self, True)
        self.make_action(self._like_action, "dislike", self, True)
        self.make_action(self._like_action, "hate", self, True)

    def _like_action(self, verb):
        rating = Person.opinion_ratings.get(verb.text, 0)
        if "do" in verb.aux or verb.punct == "?":
            # print(self.opinions)
            state = 0
            rankings = {0: []}
            for level, value in Person.opinion_ratings.items():
                rankings[value] = []
            for obj in verb.obj:
                if obj.thing in self.opinions:
                    rankings[self.opinions[obj.thing]].append(obj.text)
                else:
                    rankings[0].append(obj.text)
            response = ""
            for level, value in Person.opinion_ratings.items():
                ranking = rankings[value]
                if len(ranking) >= 1:
                    response += f"{self.called} {level}{self.tense}"
                    for rank in ranking[:-1]:
                        response += f" {rank},"
                    response = response.rstrip(",")
                    if len(ranking) != 1:
                        response += " and"
                    response += f" {ranking[-1]}. "
            ranking = rankings[0]
            if len(ranking) >= 1:
                response += f"I don't know if {self.called} "
                response += f"{verb.text}{self.tense}"
                for rank in ranking[:-1]:
                    response += f" {rank},"
                response = response.rstrip(",")
                if len(ranking) != 1:
                    response += " or"
                # I like cake, pie and math. I hate cereal. Do I like cake, pie, cereal, math, markers, and pens?
                response += f" {ranking[-1]}. "
            return response
        for obj in verb.obj:
            self.opinions[obj.thing] = rating
        return "Ok."


class SystemPersonality(Person):
    personalities = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        SystemPersonality.personalities[self.name] = self

    @classmethod
    def add_system_action(cls, action):
        for personality in cls.personalities.values():
            personality.add_action(action)

# Create objects.

with open(__file__[:-20] + "color-names/color-names.json") as color_file:
    color_list = json.load(color_file)
    for hex, name in color_list.items():
        name = name.lower()
        general_knowledge[name] = Color(name=name, color=hex)

general_knowledge["holo.birthday"] = DateTime.from_datetime_string(
    "04/12/2019 13:31:13",  # First commit date of open assistant.
    name="holo.birthday"
)
_holo = general_knowledge["holo"] = SystemPersonality(
    name="holo",  # Idea came from both holograms and [MYSTERY ;)].
    opinions=[(Thing.get_by_name("apples"), 2)],
    birthday=general_knowledge["holo.birthday"],
    called="I",
    tense=""
)
general_knowledge["prism.birthday"] = DateTime.from_datetime_string(
    "01/29/2020 14:53:25",  # Creation of test file with Prism test name.
    name="prism.birthday"
)
_prism = general_knowledge["prism"] = SystemPersonality(
    name="prism",  # Idea came from the original test triangular power symbol.
    opinions=[(Thing.get_by_name("light"), 1)],
    birthday=general_knowledge["prism.birthday"],
    called="I",
    tense=""
)
_holo.relations.append(Relation(_prism, "sister"))
_prism.relations.append(Relation(_holo, "sister"))
speaker = general_knowledge["I"] = Person(
    name="i",
    called="you",
    tense=""
)
