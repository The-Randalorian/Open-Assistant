#!/usr/bin/env python3
import os
import typing
import logging

APPLE_DIRECTORY = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
PLUGIN_DIRECTORY = APPLE_DIRECTORY + os.sep + "plugins"
COLLECTION_DIRECTORY = APPLE_DIRECTORY + os.sep + "collections"

ApplesExit: typing.NewType('ApplesExit', Exception)

_logger = logging.getLogger(f"{__name__}")

plugins = {}
services = {}
plugin_data = {}


def setup():
    _logger.warn("No setup function provided by any plugins.")
    
    
def loop():
    _logger.critical("No loop function provided by any plugins.")
    raise Exception("No loop function provided by any plugins.")
    
def cleanup():
    _logger.warn("No cleanup function provided by any plugins.")
