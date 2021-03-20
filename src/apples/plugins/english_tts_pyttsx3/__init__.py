#!/usr/bin/env python3

import os
import typing
from enum import Enum

if os.name == 'nt':
    import pythoncom
    # pythoncom.CoInitialize()

import threading
from queue import Queue
import pyttsx3
import pyttsx3.voice

import logging

from ... import plugins

core = plugins.services["core"][0]
terminal = plugins.services["terminal"][0]

_logger = logging.getLogger(f"{__name__}")

runThread: threading.Thread
thread_active = False
instruction_queue = Queue()
voices = []
voiceNames = {}


@core.setup_task
def start_speech_thread():
    global runThread, thread_active
    thread_active = True
    runThread = threading.Thread(target=speech_thread)
    runThread.daemon = True
    runThread.start()


@core.cleanup_task
def close_speech_thread():
    global runThread, instruction_queue, thread_active
    thread_active = False
    instruction_queue.join()
    runThread.join()


def speech_thread():
    global voices, voiceNames
    if os.name == 'nt':
        pythoncom.CoInitialize()
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for voice in voices:
        voiceNames[voice.name] = voice.id
    engine.setProperty('rate', 180)
    v = voiceNames.get("Cortana", None)
    if v is not None:  # default to cortana, if available
        engine.setProperty("voice", v)
    
    while True:
        command = instruction_queue.get()
        if command[0] == 0:     # say
            engine.say(command[1], command[2])
            engine.runAndWait()
        if command[0] == 1:     # set property
            engine.setProperty(command[1], command[2])
        instruction_queue.task_done()


say_parser = terminal.ArgumentParser(prog="tts.say",
                                     description="Have the text to speech engine say something.",
                                     exit_on_error=False)
say_parser.add_argument("text",
                        type=str,
                        help="Text to say.")


@terminal.command("tts.say", say_parser)
@terminal.command("say", say_parser)
def terminal_say(**kwargs):
    say(kwargs["text"])


class Color(Enum):
    voice = "voice"
    rate = "rate"
    volume = "volume"

    def __str__(self):
        return self.value


# @terminal.command("tts.say", say_parser)
# @terminal.command("say", say_parser)
'''def manual_set_property(arguments):
    global voiceNames
    prop = arguments[1]
    arguments.pop(0)
    arguments.pop(0)
    value = fix_args(arguments)
    if prop.lower() == "voice":
        v = voiceNames.get(value, None)
        if v is not None:
            value = v
    elif prop.lower() == "rate":
        value = int(value)
    elif prop.lower() == "volume":
        value = float(value)
    set_property(prop.lower(), value)'''

set_volume_parser = terminal.ArgumentParser(prog="tts.volume",
                                            description="Change the volume of the TTS engine.",
                                            exit_on_error=False)
set_volume_parser.add_argument("volume",
                               type=float,
                               help="Volume to set. Should be between 0.0 and 1.0 (inclusive).")


@terminal.command("tts.volume", set_volume_parser)
@terminal.command("volume", set_volume_parser)
def terminal_set_volume(**kwargs):
    set_volume(kwargs["volume"])


set_speed_parser = terminal.ArgumentParser(prog="tts.speed",
                                            description="Change the talking speed of the TTS engine.",
                                            exit_on_error=False)
set_speed_parser.add_argument("speed",
                              type=float,
                              help="Speed to set. 1.0 is normal speed.")


@terminal.command("tts.speed", set_speed_parser)
@terminal.command("speed", set_speed_parser)
def terminal_set_speed(**kwargs):
    set_rate(kwargs["speed"])


def get_voice_id_from_name(name: str):
    name = name.strip('"')
    try:
        return voiceNames[name]
    except KeyError:
        return None


set_voice_parser = terminal.ArgumentParser(prog="tts.voice",
                                            description="Change the voice of the TTS engine.",
                                            exit_on_error=False)
set_voice_parser.add_argument("voice",
                              type=get_voice_id_from_name,
                              default=None,
                              nargs="?",
                              help="Voice to set. Omit for a list of voices. Use double quotes around voices with multiple words.")


@terminal.command("tts.voice", set_voice_parser)
@terminal.command("voice", set_voice_parser)
def terminal_set_voice(**kwargs):
    if kwargs["voice"] is None:
        print("Available Voices:")
        for name, id in voiceNames.items():
            print(name)
    else:
        set_voice(kwargs["voice"])


def fix_args(arguments):
    s = ""
    for arg in arguments:
        if isinstance(arg, str):
            s += " " + arg
        else:
            s += " " + ".".join(arg)
    s = s.strip()
    return s

# ===================================================================
#            Standard TTS functions
# ===================================================================


def set_property(prop, value):
    global instruction_queue
    instruction_queue.put([1, prop, value])


def set_volume(value):
    set_property("volume", value)


def set_rate(value):
    set_property("rate", value)


def set_voice(value):
    set_property("voice", value)


def say(text, notification="Open Assistant"):
    global instruction_queue
    instruction_queue.put([0, text, notification])
