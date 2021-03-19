#!/usr/bin/env python3

import collections
import logging

from ... import plugins

_logger = logging.getLogger(f"{__name__}")

_setup_tasks = []
_loop_tasks = []
_cleanup_tasks = []

_event_queue = collections.deque()


def _process_event_queue():
    while True:
        try:
            task = _event_queue.popleft()
        except IndexError:
            break
        task()


def post_event(task):
    _event_queue.append(task)
    

def add_setup_task(task):
    _setup_tasks.append(task)
    _logger.debug(f"Registered setup task {task}.")


# Decorator
def setup_task(task):
    add_setup_task(task)
    return task


def add_loop_task(task):
    _loop_tasks.append(task)
    _logger.debug(f"Registered loop task {task}.")


# Decorator
def loop_task(task):
    add_loop_task(task)
    return task


def add_cleanup_task(task):
    _cleanup_tasks.append(task)
    _logger.debug(f"Registered cleanup task {task}.")


# Decorator
def cleanup_task(task):
    add_cleanup_task(task)
    return task


def setup():
    _logger.info("Running setup functions.")
    for task in _setup_tasks:
        task()
    _logger.info("Done running setup functions.")


def loop():
    _logger.debug("Running loop functions.")
    for task in _loop_tasks:
        task()
    _logger.debug("Done running loop functions.")


def cleanup():
    _logger.info("Running cleanup functions.")
    exceptions = []
    for task in _cleanup_tasks:
        try:
            task()
        except Exception as e:
            _logger.critical(f"Exception occurred while running cleanup {task}. Continuing cleanup.")
            exceptions.append(e)
    if exceptions:
        raise Exception(exceptions)
    _logger.info("Done running cleanup functions.")


plugins.setup = setup
plugins.loop = loop
plugins.cleanup = cleanup

add_loop_task(_process_event_queue)
