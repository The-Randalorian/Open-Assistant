import stanza

try:
    from .understanding import Thing
    from . import general_knowledge
except ImportError:
    from understanding import Thing
    import general_knowledge

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
        self.thing = kwargs.pop("thing", Thing.get_by_name(name=t))
        self.cases = kwargs.pop("cases", [])
        self.nummods = kwargs.pop("nummods", [])
        super().__init__(**kwargs)

    @classmethod
    def get_by_name(cls, name, **kwargs):
        return cls(thing=Thing.get_by_name(name), text=name, **kwargs)

    @classmethod
    def get_from_stanza(cls, sentence, word, **kwargs):
        case_words = get_dep_and_conj_flat(sentence, word, "case")
        cases = [Word(text=i.lemma) for i in case_words]
        nummod_words = get_dep_and_conj_flat(sentence, word, "nummod")
        nummods = [Word(text=i.lemma) for i in nummod_words]
        return cls.get_by_name(
            name=word.text,
            cases=cases,
            nummods=nummods
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
    base_subj = system_noun

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
            nsubjs = [cls.base_subj]
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
    for response in process_text(text):
        if response is not None:
            print(">>", response)


def process_text(text):
    doc = nlp(text)
    root = None

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
                    base_subj = get_dep_and_conj_flat(sentence, root, "nsubj")
                    if base_subj == ():
                        base_subj = [system_noun]
                    Noun.base_subj = base_subj
                    for root_verb in get_conjuncts(sentence, root):
                        v = Verb.get_from_stanza(sentence, root_verb)
                        for bandaid in bandaids:
                            bandaid(sentence, v)
                        if read_all_and_print:
                            print(v)
                        for subj in v.subj:
                            yield subj.thing.perform_action(v)

                    if not read_all_and_print:
                        break
                elif token.upos == "INTJ":
                    base_subj = get_dep_and_conj_flat(sentence, root, "nsubj")
                    if base_subj == ():
                        base_subj = get_dep_and_conj_flat(
                            sentence, root, "vocative")
                    if base_subj == ():
                        base_subj = [system_noun]
                    Noun.base_subj = base_subj
                    if root.lemma in ("hello", "hi", "hey"):  # and base_subj == [system_noun]:
                        yield "Hello!"


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


bandaids = [
    bandaid_turn_on_obl,
    bandaid_turn_on_nmod,
    bandaid_turn_on_weird
]

# Run this file to unpack sentences for development.
if __name__ == "__main__":
    read_all_and_print = True
    # print_process_text("Holo turn the lights on.")
    while True:
        print("="*60)
        t = input("\n: ")
        if len(t) <= 0:
            break
        print_process_text(t, False)
