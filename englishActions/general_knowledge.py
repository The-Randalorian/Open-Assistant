#!/usr/bin/env python3
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
light bulbs and other devices. There may be a few specialized classes, like
"Now", but those should only be used for specific functionality. Note this
code does NOT include any code for smart light bulbs, those are separated into
the homeAutomation plugin, since that plugin may not/will not be necessary for
all environments.

Also important to note is that these objects are, at their core,
understanding.Things. Certain objects with no real programatic meaning, such as
a "ball" won't be defined here because there is little to no use for
understanding what a "ball" is. A "ball" would therefore just be an instance of
understanding.Thing. If you create code that has some useful generic object
types, consider adding them here and making a pull request.
'''


import colorsys
import json
from datetime import datetime
from collections import namedtuple

import dateutil.tz
import gender_guesser.detector as gender

try:
    from .understanding import Thing, Action, ThingReference, ThingType
except ImportError:
    from understanding import Thing, Action, ThingReference, ThingType

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
    gender_detector = gender.Detector(case_sensitive=False)
    people = {}
    # Opinion ratings are based off the average value people place on words
    # taken in a survey. This survey is continuous, and this code will be
    # updated occasionally as new results come in. If you have an issue with
    # this ranking, feel free to contribute to the survey at
    # https://forms.office.com/Pages/ResponsePage.aspx?id=fQaEjdeackWbEBM9NkYqql39drgCDhlKtOtELsngk3VURUMwTlBUU0tVQkhUSkpFSkZKUjNCQTA5Mi4u
    opinion_ratings = {
        "love": 10,
        "worship": 9,
        "cherish": 8,
        "idolize": 7,
        "treasure": 6,
        "adore": 5,
        "prize": 4,
        "like": 3,
        "appreciate": 2,
        "enjoy": 1,
        "dislike": -1,
        "condemn": -2,
        "detest": -3,
        "abhor": -4,
        "hate": -5,
        "loath": -6,
        "despise": -7
    }
    ThingTypes = {}

    def update_pronouns(self):
        Thing.things["who"] = ThingReference(self.name)
        if self.gender == "Male":
            Thing.things["he"] = ThingReference(self.name)
        elif self.gender == "Female":
            Thing.things["she"] = ThingReference(self.name)
        else:
            Thing.things["it"] = ThingReference(self.name)

    def __init__(self, **kwargs):
        self.gender = kwargs.pop("gender", None)
        self.birthday = kwargs.pop("birthday", None)
        self.relations = kwargs.pop("relations", [])
        self.called = kwargs.pop("called", None)
        self.possessive = kwargs.pop("possessive", None)
        self.tense = kwargs.pop("tense", "s")
        self.opinions = {}
        for opinion, rating in kwargs.pop("opinions", []):
            self.opinions[opinion] = [rating]
        super().__init__(**kwargs)
        if self.called is None:
            self.called = self.name
        Person.people[self.name] = self
        for rating in self.opinion_ratings.keys():
            self.make_action(self._like_action, rating, self, True)
        if self.gender is None:
            self.gender = self.guess_gender()

    def guess_gender(self):
        gender_guess = Person.gender_detector.get_gender(self.name, "usa")
        if "female" in gender_guess:
            return "Female"
        elif "male" in gender_guess:
            return "Male"
        else:
            return "Unknown"

    def _like_action(self, verb):
        rating = self.opinion_ratings.get(verb.text, 0)
        if "do" in verb.aux or verb.punct == "?":
            rankings = {0: []}
            for level, value in Person.opinion_ratings.items():
                rankings[value] = []
            for obj in verb.obj:
                ot = obj.thing
                if ot in self.opinions:
                    rankings[self.opinions[ot]].append(getattr(ot, "called", ot.name))
                else:
                    found = False
                    for classification in ot.get_classifications():
                        classification.get_ref()
                        if classification in self.opinions:
                            found = True
                            rankings[self.opinions[classification]].append(getattr(ot, "called", ot.name))
                    if not found:
                        rankings[0].append(getattr(ot, "called", ot.name))
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
                response += f"i don't know if {self.called} "
                response += f"{verb.text}{self.tense}"
                for rank in ranking[:-1]:
                    response += f" {rank},"
                response = response.rstrip(",")
                if len(ranking) != 1:
                    response += " or"
                response += f" {ranking[-1]}. "
            return response
        for obj in verb.obj:
            self.opinions[obj.thing] = rating
        return "Ok."

    def get_classifications(self):
        yield from super().get_classifications()
        for thing_type in self.ThingTypes.values():
            if thing_type.check_is_one(self):
                yield thing_type

    @classmethod
    def boy(cls, **kwargs):
        kwargs["gender"] = "Male"
        return cls(**kwargs)

    @classmethod
    def is_boy(cls, instance):
        return cls.is_one(instance) and instance.gender == "Male"

    @classmethod
    def girl(cls, **kwargs):
        kwargs["gender"] = "Female"
        return cls(**kwargs)

    @classmethod
    def is_girl(cls, instance):
        return cls.is_one(instance) and instance.gender == "Female"

    def get_age(self):
        return 0


# Create Person special classifications
for boy_word in ["boy", "guy", "man", "dude", "gentleman"]:
    Person.ThingTypes[boy_word] = ThingType(Person, name=boy_word, constructor=Person.boy, comparison=Person.is_boy)
    continue
for girl_word in ["girl", "gal", "woman", "chick", "lady"]:
    Person.ThingTypes[girl_word] = ThingType(Person, name=girl_word, constructor=Person.girl, comparison=Person.is_girl)
    continue

Thing.things["people"] = ThingReference("person")


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
    for hex_value, name in color_list.items():
        name = name.lower()
        general_knowledge[name] = Color(name=name, color=hex_value)

general_knowledge["holo.birthday"] = DateTime.from_datetime_string(
    "04/12/2019 13:31:13",  # First commit date of open assistant.
    name="holo.birthday"
)
# noinspection PyTypeChecker
_holo = general_knowledge["holo"] = SystemPersonality(
    name="holo",  # Idea came from both holograms and [MYSTERY ;)].
    opinions=[(Thing.get_by_name("apples"), 2)],
    birthday=general_knowledge["holo.birthday"],
    called="me",
    possessive="my",
    tense=""
)

general_knowledge["prism.birthday"] = DateTime.from_datetime_string(
    "01/29/2020 14:53:25",  # Creation of test file with Prism test name.
    name="prism.birthday"
)
# noinspection PyTypeChecker
_prism = general_knowledge["prism"] = SystemPersonality(
    name="prism",  # Idea came from the original test triangular power symbol.
    opinions=[(Thing.get_by_name("light"), 1)],
    birthday=general_knowledge["prism.birthday"],
    called="me",
    possessive="my",
    tense=""
)

_holo.relations.append(Relation(_prism, "sister"))
_prism.relations.append(Relation(_holo, "sister"))
# noinspection PyTypeChecker
speaker = general_knowledge["i"] = Person(
    name="i",
    called="you",
    tense=""
)
Thing.things["you"] = ThingReference("holo")
