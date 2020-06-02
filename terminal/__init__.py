import threading
# import time
import copy
import os

services = {}
plugin = {}
core = None
runThread = None
threadActive = False
tickets = []
commands = {}
commandData = {}


def _register_(serviceList, pluginProperties):
    global services, plugin, core
    services = serviceList
    plugin = pluginProperties
    core = services["core"][0]
    core.addStart(startThread)
    core.addClose(closeThread)
    core.addLoop(loopTask)

    addCommands({
        "help": assist,
        "assist": assist,
        "estop": eStop,
        "emergency": eStop,
        # "stop": stop,
        "exit": stop,
        "terminal": {
            "help": assist,
            "assist": assist,
            "estop": eStop,
            "emergency": eStop,
            "stop": stop,
            "exit": stop}})


def process_tickets():
    global tickets
    while len(tickets) > 0:
        if tickets[0][0][0].lower() == "m":
            print(tickets[0][1])
        elif tickets[0][0][0].lower() == "q":
            tickets[0][2].get("function", print)(input(tickets[0][1]))
        elif tickets[0][0][0].lower() == "r":
            print(tickets[0][1])
        del tickets[0]


def loopTask():
    global commands
    process_tickets()
    rawCommand = input(">:").strip().split(" ")
    if len(rawCommand) > 0:
        if len(rawCommand[0]) != 0:
            quoted = False
            quotedCommand = []
            for section in range(0, len(rawCommand)):
                if quoted:
                    quotedCommand[-1] += " " + rawCommand[section]
                else:
                    if rawCommand[section][0] == '"':
                        quoted = True
                    quotedCommand.append(rawCommand[section])
                if rawCommand[section][-1] == '"':
                    quoted = False
            rawCommand = quotedCommand
            for section in range(0, len(rawCommand)):
                if rawCommand[section][0] == '"' \
                        and rawCommand[section][-1] == '"':
                    rawCommand[section] = rawCommand[section][1:-1]
                elif ("." in rawCommand[section] or section == 0):
                    rawCommand[section] = rawCommand[section].split(".")
            action = copy.deepcopy(commands)
            for part in rawCommand[0]:
                action = action.get(part, notFound)
                if callable(action):
                    break
            if callable(action):
                action(rawCommand)
            else:
                notFound(rawCommand)


def startThread():
    global runThread, threadActive
    os.system('cls' if os.name == 'nt' else 'clear')
    threadActive = True
    runThread = threading.Thread(target=threadScript)
    runThread.start()


def closeThread():
    global runThread, threadActive
    threadActive = False
    runThread.join()


def threadScript():
    global threadActive
    threadActive = False


def addTicket(action, message, **kwargs):
    tickets.append([action, message, kwargs])


def addCommands(structure):
    commands.update(structure)
    addCommandData(structure)


def addCommandData(structure, root=""):
    for alias, action in structure.items():
        if callable(action):
            if action in commandData.keys():
                commandData[action]["aliases"].append(root + alias)
            else:
                commandData[action] = {"aliases": [root + alias]}
        else:
            addCommandData(action, alias + ".")


def notFound(arguments):
    print("Command '" + ".".join(arguments[0]) + "' could not be found. Type \
help -L for a list of commands.")


def assist(arguments):
    """
INFO
    Provides helpful info for commands.
    The INFO section gives information on what the command does.
    The USAGE section describes how the command is used.
    The ALIASES section lists other aliases for the command.

USAGE
    {0} [command]
        command - Displays information on that command.

    {0} [flags]
        -h, -H - Shows this information.
        -L - Lists all available commands.
    """
    global commands
    helpCommand = arguments.pop(0)
    action = copy.deepcopy(commands)
    if len(arguments) >= 1:
        if not (type(arguments[0]) is list):
            if arguments[0][0] == "-":
                if arguments[0] == "-h" or arguments[0] == "-H":
                    assist([helpCommand, "help"])
                elif arguments[0] == "-L":
                    printCommands(commands)
                else:
                    print("Invalid flag. Type 'help help' for more info.")
                return
            arguments[0] = [arguments[0]]
        for part in arguments[0]:
            action = action.get(part, notFound)
            if callable(action):
                break
        if callable(action) and action != notFound:
            print(action.__doc__.format(".".join(arguments[0])))
            print("ALIASES")
            for alias in commandData[action]["aliases"]:
                print(" " * 4 + alias)
        else:
            print("could not find command.")
    else:
        print("command not specified. Type 'help help' for more info or 'help \
-L' for a list of commands.")


def printCommands(coms, head=""):
    for command in coms.keys():
        if isinstance(coms[command], dict):
            printCommands(coms[command], head + command + ".")
        else:
            print(head + command)


def eStop(arguments):
    """
INFO
    Triggers an emergency stop. This will close the entire program.

USAGE
    {0}
    """
    core.eStop()


def stop(arguments):
    """
INFO
    Triggers a regular stop. This will close the entire program.

USAGE
    {0}
    """
    core.stop()
