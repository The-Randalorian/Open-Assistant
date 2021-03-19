#!/usr/bin/env python3

import collections
import functools
import logging
import shlex
import argparse
import sys

from ... import plugins

core = plugins.services["core"][0]

_logger = logging.getLogger(f"{__name__}")

Command = collections.namedtuple("Command", ["name", "function", "arg_parser"], defaults=[None])
_commands = {}


class TerminalExit(Exception):
    pass


class ArgumentParser(argparse.ArgumentParser):
    def exit(self, status=0, message=None):
        if message:
            self._print_message(message, sys.stderr)
        raise TerminalExit

@core.loop_task
def _get_input():
    command_string = input(">:")
    command_arguments = shlex.split(command_string, posix=False)
    _logger.debug(f"Interpreted command string \"{command_string}\" as {command_arguments}.")
    try:
        com = _commands[command_arguments[0]]
    except IndexError:
        _logger.debug("No command entered.")
        return
    except KeyError:
        print(f"Unrecognized command \"{command_arguments[0]}\".")
        return
    if com.arg_parser is None:
        com.function(arguments=command_arguments)
    else:
        kwargs = {}
        try:
            ns = com.arg_parser.parse_args(command_arguments[1:])
            kwargs = vars(ns)
        except argparse.ArgumentError as argument_error:
            raise argument_error
        except TerminalExit:
            return
        com.function(arguments=command_arguments, **kwargs)

def create_command(function, name, arg_parser=None):
    com = Command(name, function, arg_parser)
    add_command(com)
    return function


def add_command(com):
    _logger.debug(f"Registered command {com}.")
    _commands[com.name] = com


# Decorator
def command(name, arg_parser=None):
    return functools.partial(create_command, name=name, arg_parser=arg_parser)


assist_parser = ArgumentParser(prog="terminal.assist",
                               description="Provide help information to the user.",
                               epilog="terminal.assist is also known as terminal.help.",
                               exit_on_error=False)
assist_action_group = assist_parser.add_mutually_exclusive_group(required=True)
assist_action_group.add_argument("-l",
                                 "--list",
                                 help="List all commands.",
                                 action="store_true")
assist_action_group.add_argument("command", nargs="?",
                                 help="Command to show help info for.")


@command("terminal.assist", assist_parser)
@command("assist", assist_parser)
@command("terminal.help", assist_parser)
@command("help", assist_parser)
def assist(**kwargs):
    if kwargs.get("list", False):
        for command_name in sorted(_commands.keys()):
            print(command_name)
        return
    command_name = kwargs.get("command", None)
    if command_name is not None:
        com = _commands[command_name]
        try:
            com.arg_parser.print_help()
        except AttributeError:
            print(f"No help info available for {command_name}.")
        return


close_parser = ArgumentParser(prog="terminal.close",
                              description="Exit the program.",
                              epilog="terminal.close is also known as terminal.exit.",
                              exit_on_error=False)


@command("terminal.close", close_parser)
@command("close", close_parser)
@command("terminal.exit", close_parser)
@command("exit", close_parser)
def close(**_):
    raise plugins.ApplesExit(0, "Terminal exit")
