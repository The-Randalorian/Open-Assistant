# import threading
# import time
import logging
import hashlib
import os
import types

# from sqlalchemy import Column, Integer, String, LargeBinary, Boolean, ForeignKey, create_engine, Sequence, Enum
# from sqlalchemy.orm import backref, sessionmaker, scoped_session, Session
import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative
import sqlalchemy.ext.associationproxy
import sqlalchemy.exc

from . import implementation

_logger = logging.getLogger(__name__)

class SQLThingStorage(actions.packaging.ThingStorage):
    def __init__(self):
        self.engine = None
        self.root_user = None
        self.user = None

    def connect(self, database_url):
        # Create a connection to the database
        self.engine = sqlalchemy.create_engine(
            database_url,
            echo=False)
        # Run the implementation setup. This makes sure that the database is configured properly. It will attempt to
        # create the correct tables if they don't exist.
        self.root_user = implementation.setup(self.engine)

    def login(self, username, password):
        try:
            # Get the data needed to validate the user.
            user = self.session.query(implementation.User).filter_by(user_name=username).first()
            # Try to authenticate the user. If an assertion fails, the user will be denied.
            assert user.auth_method in implementation.valid_authentications, "Invalid authentication method."
            if user.auth_method == implementation.AuthMethods.internal_password_00_01:
                assert implementation.hash_password(password, user.password_salt) == user.password_hash, "Invalid password."
            self.user = user
        except AssertionError as error:
            logging.warning(f"Invalid authentication: \"{error}\"")

    def create_user(self, username, password, email="donotreply@donotreply.net"):
        try:
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
                session.commit(user)
        except sqlalchemy.exc.SQLAlchemyError as e:
            raise e


    def start_session(self):
        assert self.root_user is not None, "Not connected to a server."
        assert self.user is not None, "Not logged in to a server."
        return SQLThingStorageSession(self)


class SQLThingStorageSession(actions.packaging.ThingStorage):
    def __init__(self, master):
        self.master = master
        self.sql_session = sqlalchemy.orm.Session(self.master.engine)
        self.user = self.master.user

    def get_data(self, name):
        _logger.debug("getting", name)
        object = self.session.query(implementation.Thing).filter_by(thing_key=name, owner_id=self.user.user_id).first()
        if object:
            data = object.thing_data
            return data
        else:
            object = self.session.query(implementation.Thing).filter_by(thing_key=name, owner_id=self.user.user_id).first()
            if object:
                data = object.thing_data
                return data
            else:
                return None

    def put_data(self, name, data):
        _logger.debug("putting", name, len(data))
        hash = sha512(data)
        object = self.session.query(Thing).get(name)
        if not object:
            _logger.debug("making", name)
            object = implementation.Thing(thing_key=name, owner_id=user.user_id, thing_data=data, thing_data_checksum=hash,
                           encrypted=False)
            self.session.add(object)
        else:
            object.thing_data = data
            object.thing_data_checksum = hash
            object.encrypted = False