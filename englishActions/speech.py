#!/usr/bin/env python3
'''
The purpose of speech.py is to begin to interpret sentences into what is
intended. It's goal IS NOT to directly figure out EXACTLY what needs to
happen, but is instead to figure out "what needs to do what". It then
grabs Thing instances and then passes it off to their Actions for further
processing and intent comprehension.

This is primarily done through the Stanza library, which unpacks sentences
into parts of speech, relationships and other information. This library makes
some frequent (but understandable, see later comment near bandaids) mistakes
that need to be fixed before handling by actions. These are handled by the
bandaid functions also included here.
'''
import itertools

import stanza

try:
    from . import understanding
    from . import general_knowledge
    from . import thesaurus
except ImportError:
    import understanding
    import general_knowledge
    import thesaurus

read_all_and_print = (__name__ == "__main__")
stanza_package = 'default'
try:
    # Attempt to create the pipeline without logging errors. If it can't be
    # found, log at full logging level.
    nlp = stanza.Pipeline('en', package=stanza_package, logging_level='WARN')
except FileNotFoundError:
    stanza.download('en', package=stanza_package)
    nlp = stanza.Pipeline('en', package=stanza_package)


class Word:
    def __init__(self, **kwargs):
        self.text = kwargs.pop("text")
        self.stanza = kwargs.pop("stanza", None)
        super().__init__(**kwargs)

    def __str__(self):
        return self.text

    def __repr__(self):
        return str(self)


class Noun(Word):
    def __init__(self, **kwargs):
        t = kwargs.get("text")
        self.thing = kwargs.pop("thing", understanding.Thing.get_by_name(name=t))
        self.cases = kwargs.pop("cases", [])
        self.nummods = kwargs.pop("nummods", [])
        super().__init__(**kwargs)

    @classmethod
    def get_by_name(cls, name, called=None, **kwargs):
        t = understanding.Thing.get_by_name(name)
        if called is not None:
            t.called = getattr(t, "called", called)
        return cls(thing=t, text=name, **kwargs)

    @classmethod
    def get_from_stanza(cls, sentence, word, **kwargs):
        case_words = get_dep_and_conj_flat(sentence, word, "case")
        cases = [Word(text=i.lemma.lower()) for i in case_words]
        nummod_words = get_dep_and_conj_flat(sentence, word, "nummod")
        nummods = [Word(text=i.lemma.lower()) for i in nummod_words]
        return cls.get_by_name(
            name=word.lemma.lower(),
            cases=cases,
            nummods=nummods,
            called=word.text.lower()
            )

    def __str__(self):
        s = f"{self.text}"
        s += f"\n    - cases: {self.cases}"
        s += f"\n    - nummods: {self.nummods}"
        return s

    def __repr__(self):
        s = f"\n        {self.text}"
        s += f"\n            - cases: {self.cases}"
        s += f"\n            - nummods: {self.nummods}"
        return s + "\n        "


system_noun = Noun.get_by_name("holo")


class Verb(Word):
    base_subjs = [system_noun]

    def __init__(self, **kwargs):
        self.subj = kwargs.pop("subj", [system_noun])
        self.obj = kwargs.pop("obj", [])
        self.obl = kwargs.pop("obl", [])
        self.iobj = kwargs.pop("iobj", [])
        self.advmod = kwargs.pop("advmod", [])
        self.aux = kwargs.pop("aux", [])
        self.punct = kwargs.pop("punct", ".")
        super().__init__(**kwargs)

    @classmethod
    def get_from_stanza(cls, sentence, word, **kwargs):
        subjects = list(get_dep_and_conj_flat(sentence, word, "nsubj"))
        if len(subjects) <= 0:
            nsubjs = cls.base_subjs
        else:
            nsubjs = []
            for ob in subjects:
                nsubjs.append(Noun.get_from_stanza(sentence, ob))
        obls = []
        for ob in get_dep_and_conj_flat(sentence, word, "obl"):
            obls.append(Noun.get_from_stanza(sentence, ob))
        objs = []
        for ob in get_dep_and_conj_flat(sentence, word, "obj"):
            objs.append(Noun.get_from_stanza(sentence, ob))
        iobjs = []
        for ob in get_dep_and_conj_flat(sentence, word, "iobj"):
            iobjs.append(Noun.get_from_stanza(sentence, ob))
        advmods = []
        for advmod in get_dep_and_conj_flat(sentence, word, "advmod"):
            advmods.append(advmod.lemma)
        auxs = []
        for aux in get_dep_and_conj_flat(sentence, word, "aux"):
            auxs.append(aux.lemma)
        punctuation = list(get_dep_and_conj_flat(sentence, word, "punct"))
        if len(punctuation) <= 0:
            punct = "."
        else:
            punct = punctuation[0].lemma
        return Verb(
            text=word.lemma,
            subj=nsubjs,
            obl=obls,
            obj=objs,
            iobj=iobjs,
            advmod=advmods,
            aux=auxs,
            punct=punct,
            stanza=word
             )

    def __str__(self):
        s = f"{self.text}\n"
        s += f"    - subj: {self.subj}\n"
        s += f"    - obj: {self.obj}\n"
        s += f"    - iobj: {self.iobj}\n"
        s += f"    - obl: {self.obl}\n"
        s += f"    - advmod: {self.advmod}\n"
        return s


def print_process_text(text, reprint=True):
    if reprint:
        print(": " + text)
    last_was_ok = False
    for response in process_text(text):
        if response.lower().strip() == "ok.":
            last_was_ok = True
            continue
        if response is not None:
            if last_was_ok:
                print(">>", "ok.")
            print(">>", response)
        last_was_ok = False
    if last_was_ok:
        print(">>", "ok.")

def run_root(sentence, root, default_subjects=[system_noun]):
    subjects = list(get_dep_and_conj_flat(sentence, root, "nsubj"))
    if len(subjects) <= 0:
        nsubjs = list(default_subjects)
    else:
        nsubjs = []
        for ob in subjects:
            nsubjs.append(Noun.get_from_stanza(sentence, ob))
    Verb.base_subjs = nsubjs
    for root_verb in get_conjuncts(sentence, root):
        v = Verb.get_from_stanza(sentence, root_verb)
        for bandaid in post_bandaids:
            bandaid(sentence, v)
        if read_all_and_print:
            print(v)
        for subj in v.subj:
            yield subj.thing.perform_action(v)


def ask_is_one(sentence, root):
    nsubjs = get_dep_and_conj_flat(sentence, root, "nsubj")
    nsubjs = [Noun.get_from_stanza(sentence, nsubj) for nsubj in nsubjs]
    for classification in get_conjuncts(sentence, root):
        class_noun = Noun.get_from_stanza(sentence, classification)
        for nsubj in nsubjs:
            yield class_noun.thing.ask_is_one(nsubj.thing)


def process_text(text):
    text = text.strip().lower()
    print(repr(text))
    doc = nlp(text)
    root = None
    Verb.base_subjs = [system_noun]

    for sentence in doc.sentences:
        for token in sentence.words:
            if read_all_and_print:
                print(token.id,
                      token.lemma,
                      token.deprel,
                      token.upos,
                      token.head)
            if token.deprel == "root":
                root = token
                if token.upos == "VERB":
                    yield from run_root(sentence, root)
                elif token.upos == "INTJ":
                    base_subj = get_dep_and_conj_flat(sentence, root, "nsubj")
                    if base_subj == ():
                        base_subj = get_dep_and_conj_flat(
                            sentence, root, "vocative")
                    if base_subj == ():
                        base_subj = [system_noun]
                    Verb.base_subjs = [base_subj]
                    if root.lemma in ("hello", "hi", "hey"):  # and base_subj == [system_noun]:
                        yield "Hello!"
                elif token.upos == "NOUN":
                    for root in get_conjuncts(sentence, root):
                        base_subj = list(get_dep_and_conj_flat(sentence, root, "nsubj"))
                        determiners = get_dep_and_conj_flat(sentence, root, "det")
                        asking = False
                        for copula in get_dep_and_conj_flat(sentence, root, "cop"):
                            if copula.id < base_subj[0].id:
                                yield from ask_is_one(sentence, root)
                                asking = True
                        if asking:
                            continue
                        for punct in get_dep_and_conj_flat(sentence, root, "punct"):
                            if punct.lemma == "?":
                                yield from ask_is_one(sentence, root)
                                asking = True
                        if asking:
                            continue
                        base_subj = [Noun.get_from_stanza(sentence, nsubj) for nsubj in base_subj]
                        for determiner in determiners:
                            if determiner.lemma in ("a", "an"):
                                for subj in base_subj:
                                    yield subj.thing.classify(root.lemma)
                        for clause in itertools.chain(
                                get_dep_and_conj_flat(sentence, root, "acl"),
                                get_dep_and_conj_flat(sentence, root, "acl:relcl")):
                            if clause.upos == "VERB":
                                yield from run_root(sentence, clause, default_subjects=base_subj)



def get_conjuncts(sentence, primary):
    yield primary
    for word in get_dependency(sentence, primary, 'conj'):
        yield word


def get_dependency(sentence, head, dependency):
    for word in sentence.words:
        if word.head == int(head.id) and word.deprel == dependency:
            yield word


def get_dep_and_conj_flat(sentence, head, dependency):
    primaries = get_dependency(sentence, head, dependency)
    for primary in primaries:
        for conjunct in get_conjuncts(sentence, primary):
            yield conjunct


# These are various fixes that need to be applied to verbs before executing.
# I hate this, but many common sentences aren't 'quite' interpreted properly by
# Stanza (yes I have tested all english packages). This is not entirely
# Stanza's fault, as it usually is a context thing. A good example is  "Turn
# on the lights." Grammatically speaking, you could either be saying change the
# lights to on (probably correct), or stand on top of the lights and do a spin.
# Technically both are correct, however one is probably not what is intended.
# These bandaids are designed to recognize these situations and correct them.
# Like the name implies, these are small, targeted fixes for common edge cases,
# and therefore should be fixed properly when possible. ('fixed properly' will
# probably mean retraining some model with better/different data). These
# functions and the list they are added to are public. If your verb has some
# weird cases, add on to the bandaids list to add your checks.


def bandaid_turn_on_obl(sentence, verb):
    if verb.text in ("turn", "switch", "toggle", "set") \
            and len(verb.obj) <= 0 and len(verb.obl) > 0:
        obls = verb.obl
        verb.obl = []
        for obl in obls:
            for case_index, case in enumerate(obl.cases):
                if case.text in ("on", "off"):
                    verb.advmod.append(obl.cases.pop(case_index).text)
            verb.obj.append(obl)


def bandaid_turn_on_nmod(sentence, verb):
    if verb.text in ("turn", "switch", "toggle") \
            and len(verb.obj) <= 0 and len(verb.advmod) <= 0:
        for word in sentence.words:
            if word.lemma in ("on", "off") \
                    and sentence.words[word.head-1].deprel == "nmod":
                verb.advmod.append(word.lemma)
            elif word.deprel == "nmod" and word.head == int(verb.stanza.id):
                verb.obj.append(Noun.get_from_stanza(sentence, word))


def bandaid_turn_on_weird(sentence, verb):
    if verb.text in ("turn", "switch", "toggle") \
            and len(verb.advmod) <= 0:
        for word in sentence.words:
            if word.lemma in ("on", "off") \
                    and word.deprel == "compound:prt" \
                    and word.head == int(verb.stanza.id):
                verb.advmod.append(word.lemma)


post_bandaids = [
    bandaid_turn_on_obl,
    bandaid_turn_on_nmod,
    bandaid_turn_on_weird
]

# Run this file to unpack sentences for development.
if __name__ == "__main__":
    import time
    read_all_and_print = False
    # These test cases are run automatically to demonstrate and test text unpacking.
    _test_cases = '''i like cake, pie and math but i hate cereal. i love books and movies. do i like cake, pie, cereal, markers, movies, and pens?
                     john is a person. john loves anime and manga. john hates people, music and cleaning. does john dislike anime, cleaning, you and me?
                     don is a guy who likes anime. does don love anime and movies?
                     hannah is a girl who loves books and art. does she hate movies and books?
                     jake is a person who loves anime and hates me. does he love me and anime?
                     amanda is a girl who loves books. harold is a guy who hates homework. does amanda hate books and does harold love homework?
                     susan is a woman who adores dogs and bob is a person who hates apples. do he and susan love dogs and apples?'''
    if False:  # Change this line to disable the built in test case checking.
        for line in _test_cases.splitlines(False):
            print("=" * 60)
            print_process_text(line.strip())
            time.sleep(1)
    while True:
        print("="*60)
        t = input("\n: ")
        if len(t) <= 0:
            break
        print_process_text(t, False)
