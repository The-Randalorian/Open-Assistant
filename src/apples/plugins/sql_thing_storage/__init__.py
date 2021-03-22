#!/usr/bin/env python3

import logging

from ... import plugins

from . import administration

_logger = logging.getLogger(f"{__name__}")

terminal = plugins.services["terminal"][0]
actions = plugins.services["actions"][0]

login_parser = terminal.ArgumentParser(prog="sqlts.login",
                                       description="Login to a SQL Thing Storage server.",
                                       exit_on_error=False)
login_parser.add_argument("database",
                         help="Database URL.")
login_parser.add_argument("username",
                         help="Open Assistant username.")
login_parser.add_argument("password",
                         help="Open Assistant password.")


@terminal.command("sqlts.login", login_parser)
def terminal_login(**kwargs):
    server = administration.SQLThingStorageServer(kwargs["database"])
    storage = server.login(kwargs["username"], kwargs["password"])
    print(storage, str(storage))
    actions.storage.set_default_storage(storage)


create_user_parser = terminal.ArgumentParser(prog="sqlts.create_user",
                                       description="Create a new user for a SQL Thing Storage server.",
                                       exit_on_error=False)
create_user_parser.add_argument("database",
                                help="Database URL.")
create_user_parser.add_argument("username",
                                help="Open Assistant username.")
create_user_parser.add_argument("password",
                                help="Open Assistant password.")
create_user_parser.add_argument("email",
                                nargs="?",
                                default="donotreply@donotreply.net",
                                help="Open Assistant email.")


@terminal.command("sqlts.create_user", create_user_parser)
def terminal_create_user(**kwargs):
    server = administration.SQLThingStorageServer(kwargs["database"])
    storage = server.create_user(kwargs["username"], kwargs["password"])
    actions.storage.set_default_storage(storage)
