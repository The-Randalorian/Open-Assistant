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
core = None
tts = None
tts_say = None


def _register_(serviceList, pluginProperties):
    global services, plugin, core, tts, tts_say
    services = serviceList
    plugin = pluginProperties
    core = services["core"][0]
    tts = services["tts"][0]
    tts_say = tts.say
    services["userInterface"][0].addCommands({
        "converse": textConverse,
        "actions": {
            "converse": textConverse
            }
        })


def loopTask():
    pass


def textConverse(arguments):
    """
INFO
    Starts up a conversation using the terminal

USAGE
    {0}
    """
    conversing = True
    while conversing:
        t = input("USER:> ")
        if t:
            process_text(t, [print, tts_say])
        else:
            break


def process_text(text, replies=None):
    global tts, nlp
    if replies is None:
        replies = [tts_say]
    for response in speech.process_text(text):
        if response is None:
            response = "Ok."
        for reply in replies:
            reply(response)
