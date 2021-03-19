#!/usr/bin/env python3

import logging

from ... import plugins

core = plugins.services["core"][0]

_logger = logging.getLogger(f"{__name__}")