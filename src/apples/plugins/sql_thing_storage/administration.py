#!/usr/bin/env python3

import logging
import os
import typing

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative
import sqlalchemy.ext.associationproxy
import sqlalchemy.exc

from . import implementation

from ... import plugins

actions = plugins.services["actions"][0]
understanding = actions.understanding
storage = actions.storage

_logger = logging.getLogger(f"{__name__}")


class SQLThingStorageServer:
    """
    A quite literal representation of a SQLThingStorageServer.
    """
    def __init__(self, database_url):
        """
        Create an instance and connect to the given database. The required tables and root user will be created
        automatically when needed.
        """
        _logger.info("Connecting to SQL database")
        self.engine = sqlalchemy.create_engine(database_url,
                                               echo=False)
        self.root_user = implementation.setup(self.engine)
        _logger.info("Connected to SQL database.")

    def create_user(self, username: str, password: str, email: str = "donotreply@donotreply.net") -> "SQLThingStorage":
        """
        Create a new user on the server. Returns a SQLThingStorage instance logged in as that user. Will give an error
        if not successful.
        """
        try:
            _logger.info(f"Creating user '{username}'")
            with sqlalchemy.orm.Session(self.engine) as session:
                pass_salt = os.urandom(64)
                encr_salt = os.urandom(64)
                user = implementation.User(
                    user_name=username,
                    password_hash=implementation.hash_password(password, pass_salt),
                    password_salt=pass_salt,
                    encryption_salt=encr_salt,
                    auth_method=implementation.AuthMethods.internal_password_00_01,
                    email=email)
                session.add(user)
                session.commit()
            _logger.info(f"Created user '{username}'")
            return self.login(username, password)
        except sqlalchemy.exc.SQLAlchemyError as e:
            _logger.warning(f"Error creating user '{username}'")
            raise e

    def login(self, username: str, password: str) -> "SQLThingStorage":
        """
        Login as a user on the server. Returns a SQLThingStorage instance logged in as that user. Will give an error if
        not successful.
        """
        # Get the data needed to validate the user.
        with sqlalchemy.orm.Session(self.engine) as session:
            _logger.info(f"Logging in as user '{username}'")
            user = session.query(implementation.User).filter_by(user_name=username).first()
            # Try to authenticate the user. If an assertion fails, the login will be denied.
            assert user is not None, \
                "User does not exist."
            assert user.auth_method in implementation.valid_authentications, \
                "Invalid authentication method. This user cannot be logged in."
            if user.auth_method == implementation.AuthMethods.internal_password_00_01:
                _logger.info(f"Logging in user '{username}' using authentication method internal_password_00_01.")
                assert implementation.hash_password(password, user.password_salt) == user.password_hash, \
                    "Invalid password."
            _logger.info(f"Logged in as user '{username}'")
            return SQLThingStorage(server=self, user=user)


class SQLThingStorage(storage.OptimizedThingStorage):

    def __init__(self, server: SQLThingStorageServer, user: implementation.User):
        self.server = server
        self.user = user

    def start_session(self) -> "SQLThingStorageSession":
        return SQLThingStorageSession(self)


class SQLThingStorageSession(storage.OptimizedThingStorageSession):
    def __init__(self, master: SQLThingStorage):
        super().__init__(master)

        self.server = self.master.server
        self.user = self.master.user
        self.root_user = self.server.root_user

        self.sql_session = sqlalchemy.orm.Session(self.server.engine)

    def get_data(self, name: str) -> typing.Optional[bytes]:
        _logger.debug(f"Getting {name}")
        sql_thing = self.sql_session.query(implementation.Thing).get((self.user.user_id, name))
        if sql_thing:
            data = sql_thing.thing_data
            return data
        else:
            sql_thing = self.sql_session.query(implementation.Thing).get((self.user.user_id, name))
            if sql_thing:
                data = sql_thing.thing_data
                return data
            else:
                return None

    def put_data(self, name: str, data: bytes):
        _logger.debug(f"Putting {name}")
        checksum = implementation.hash_thing_data(data)
        sql_thing = self.sql_session.query(implementation.Thing).get((self.user.user_id, name))
        if not sql_thing:
            _logger.debug("making", name)
            sql_thing = implementation.Thing(thing_key=name,
                                             owner_id=self.user.user_id,
                                             thing_data=data,
                                             thing_data_checksum=checksum,
                                             encrypted=False)
            self.sql_session.add(sql_thing)
        else:
            sql_thing.thing_data = data
            sql_thing.thing_data_checksum = checksum
            sql_thing.encrypted = False

    def delete_data(self, name: str):
        pass

    def commit_data(self):
        self.sql_session.commit()
