#!/usr/bin/env python3

import logging

from ... import plugins

try:
    from . import understanding
    from . import general_knowledge
    from . import speech
except ImportError:
    import understanding
    import general_knowledge
    import speech

services = {}
plugin = {}

core = plugins.services["core"][0]
terminal = plugins.services["terminal"][0]
tts = plugins.services["tts"][0]

_logger = logging.getLogger(f"{__name__}")


converse_parser = terminal.ArgumentParser(prog="actions.converse",
                               description="Starts up a conversation using the terminal",
                               exit_on_error=False)


@terminal.command("actions.converse", converse_parser)
@terminal.command("converse", converse_parser)
def text_converse(arguments):
    conversing = True
    while conversing:
        t = input("USER:> ")
        if t:
            process_text(t, [print, tts.say])
        else:
            break


def process_text(text, reply_methods=None):
    global tts
    if reply_methods is None:
        reply_methods = [tts.say]
    for response in speech.process_text(text):
        if response is None:
            response = "Ok."
        for reply_method in reply_methods:
            reply_method(response)
