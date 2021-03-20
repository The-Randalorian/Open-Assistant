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

import enum

base = sqlalchemy.ext.declarative.declarative_base()

_logger = logging.getLogger(__name__)

'''class Group(base):
    __tablename__ = "groups"
    group_id = Column(Integer(), primary_key=True)
    group_name = Column(String(32), unique=True)
    owner_id = Column(Integer(), ForeignKey('users.user_id'))'''


class AuthMethods(enum.Enum):
    internal_unknown = 0x00000000
    internal_disabled = 0x00000010
    internal_password_unknown = 0x00010000
    internal_password_00_01 = 0x00010001
    # django_unknown = 0x01000000


class Group(base):
    __tablename__ = "oa_groups"
    group_id = sqlalchemy.Column(
        sqlalchemy.Integer(),
        sqlalchemy.Sequence('group_id_seq'),
        primary_key=True
    )
    group_name = sqlalchemy.Column(
        sqlalchemy.String(128),
        unique=True
    )
    owner_id = sqlalchemy.Column(
        sqlalchemy.Integer(),
        sqlalchemy.ForeignKey('oa_users.user_id'),
        nullable=False,
    )
    users = sqlalchemy.orm.relationship(
        "UserGroups",
        back_populates="group"
    )
    __table_args__ = (
        {
            "comment": "Open Assistant - Groups"
        },
    )


class User(base):
    __tablename__ = 'oa_users'
    user_id = sqlalchemy.Column(
        sqlalchemy.Integer(),
        sqlalchemy.Sequence('user_id_seq'),
        primary_key=True
    )
    user_name = sqlalchemy.Column(
        sqlalchemy.String(32),
        unique=True
    )
    password_hash = sqlalchemy.Column(
        sqlalchemy.LargeBinary(64)
    )
    password_salt = sqlalchemy.Column(
        sqlalchemy.LargeBinary(64)
    )
    encryption_salt = sqlalchemy.Column(
        sqlalchemy.LargeBinary(64)
    )
    email = sqlalchemy.Column(
        sqlalchemy.String(254)
    )
    # Apparently the maximum usable email address length, see
    # https://7php.com/the-maximum-length-limit-of-an-email-address-is-254-not-320
    # for reason
    auth_method = sqlalchemy.Column(
        sqlalchemy.Enum(AuthMethods),
        default=AuthMethods.internal_password_00_01
    )
    groups = sqlalchemy.orm.relationship(
        "UserGroups",
        back_populates="user"
    )
    things = sqlalchemy.orm.backref(
        "Thing",
        back_populates="owner"
    )
    __table_args__ = (
        {
            "comment": "Open Assistant - Users"
        },
    )


class UserGroups(base):
    __tablename__ = 'oa_user_groups'
    user_id = sqlalchemy.Column(
        sqlalchemy.Integer(),
        sqlalchemy.ForeignKey('oa_users.user_id'),
        primary_key=True
    )
    group_id = sqlalchemy.Column(
        sqlalchemy.Integer(),
        sqlalchemy.ForeignKey('oa_groups.group_id'),
        primary_key=True
    )
    role = sqlalchemy.Column(
        sqlalchemy.String(32),
    )
    permissions = sqlalchemy.Column(
        sqlalchemy.String(32),
    )
    user = sqlalchemy.orm.relationship(
        "User",
        back_populates="groups"
    )
    group = sqlalchemy.orm.relationship(
        "Group",
        back_populates="users"
    )
    __table_args__ = (
        {
            "comment": "Open Assistant - Users' Groups"
        },
    )


class Thing(base):
    __tablename__ = 'oa_things'
    owner_id = sqlalchemy.Column(
        sqlalchemy.Integer(),
        sqlalchemy.ForeignKey('oa_users.user_id'),
        primary_key=True
    )
    thing_key = sqlalchemy.Column(
        sqlalchemy.String(255),
        primary_key=True
    )
    thing_data = sqlalchemy.Column(
        sqlalchemy.LargeBinary(65535)
    )
    thing_data_checksum = sqlalchemy.Column(
        sqlalchemy.LargeBinary(65535)
    )
    encrypted = sqlalchemy.Column(
        sqlalchemy.Boolean()
    )
    group_permissions = sqlalchemy.orm.relationship(
        "ThingGroupPermissions",
        back_populates="owner"
    )
    user_permissions = sqlalchemy.orm.relationship(
        "ThingUserPermissions",
        back_populates="owner"
    )
    __table_args__ = (
        {
            "comment": "Open Assistant - Stored Thing Objects"
        },
    )


class ThingGroupPermissions(base):
    __tablename__ = 'oa_thing_group_permissions'
    owner_id = sqlalchemy.Column(
        sqlalchemy.Integer(),
        primary_key=True
    )
    thing_key = sqlalchemy.Column(
        sqlalchemy.String(32),
        primary_key=True
    )
    group_id = sqlalchemy.Column(
        sqlalchemy.Integer(),
        sqlalchemy.ForeignKey('oa_groups.group_id'),
        primary_key=True
    )
    permissions = sqlalchemy.Column(
        sqlalchemy.String(8),
    )
    owner = sqlalchemy.orm.relationship(
        "Thing",
        back_populates="group_permissions"
    )
    __table_args__ = (
        sqlalchemy.ForeignKeyConstraint(
            (owner_id, thing_key),
            (Thing.owner_id, Thing.thing_key)
        ),
        {
            "comment": "Open Assistant - Thing Objects' Group Permissions"
        },
    )


class ThingUserPermissions(base):
    __tablename__ = 'oa_thing_user_permissions'
    owner_id = sqlalchemy.Column(
        sqlalchemy.Integer(),
        primary_key=True
    )
    thing_key = sqlalchemy.Column(
        sqlalchemy.String(32),
        primary_key=True
    )
    target_id = sqlalchemy.Column(
        sqlalchemy.Integer(),
        sqlalchemy.ForeignKey('oa_users.user_id'),
        primary_key=True
    )
    permissions = sqlalchemy.Column(
        sqlalchemy.String(8),
    )
    owner = sqlalchemy.orm.relationship(
        "Thing",
        back_populates="user_permissions"
    )
    __table_args__ = (
        sqlalchemy.ForeignKeyConstraint(
            (owner_id, thing_key),
            (Thing.owner_id, Thing.thing_key)
        ),
        {
            "comment": "Open Assistant - Things' User Permissions"
        },
    )


services = {}
plugin = {}
core = types.ModuleType
actions = types.ModuleType
engine: sqlalchemy.engine.Engine
session_maker: sqlalchemy.orm.sessionmaker
session_scope: sqlalchemy.orm.scoped_session
session: sqlalchemy.orm.Session
root_user: User
user: User
encryption_key = b'\x00'*64
SQLThingStorage: type  # OOP at it's finest the type of a class is type.


def _register_(serviceList, pluginProperties):
    global services, plugin, core, actions, engine, session_maker, session_scope, session, root_user, user, encryption_key
    services = serviceList
    plugin = pluginProperties
    core = services["core"][0]
    actions = services["actions"][0]
    #core.addStart(start_thread)
    #core.addClose(closeThread)
    #core.addLoop(loopTask)

    #engine = create_engine('sqlite:///:memory:', echo=True)
    with open(__file__[:-11] + "sql_urls.txt", 'r+') as f:
        database_url = f.readline().strip()
        username = f.readline().strip()
        password = f.readline().strip()
        email = f.readline().strip()
    if not database_url:
        database_url = "sqlite:///:memory:"
    engine = sqlalchemy.create_engine(
        database_url,
        echo=False)
    base.metadata.create_all(engine)
    session_maker = sqlalchemy.orm.sessionmaker(bind=engine)
    #session_scope = scoped_session(sessionmaker)
    #session = session_scope()
    session = session_maker()
    root_user = session.query(User).filter_by(user_name='/').first()
    if root_user is None:
        root_user = User(
            user_id=0,
            user_name="/",
            password_hash=b"\x00"*64,
            password_salt=b"\x00"*64,
            encryption_salt=b"\x00"*64,
            email="donotreply@donotreply.net")
        session.add(root_user)
        session.commit()
    user = session.query(User).filter_by(user_name=username).first()
    if user is None:
        pass_salt = os.urandom(64)
        encr_salt = os.urandom(64)
        user = User(
            user_name=username,
            password_hash=hash_password(password, pass_salt),
            password_salt=pass_salt,
            encryption_salt=encr_salt,
            email=email)
        session.add(user)
        session.commit()
    if hash_password(password, user.password_salt) != user.password_hash:
        raise Exception("Incorrect Login Info")
    encryption_key = get_encryption_key(password, user.encryption_salt)
    create_thing_storage()
    actions.packaging.set_thing_storage(SQLThingStorage())


def hash_password(password, salt):
    hasher = hashlib.sha512()
    hasher.update(password.encode("utf-8"))
    pass_hash = hasher.digest()
    return hashlib.pbkdf2_hmac("sha512", pass_hash, salt, 100000)


def get_encryption_key(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)


def sha512(byte_string):
    hasher = hashlib.sha512()
    hasher.update(byte_string)
    return hasher.digest()

def sha256(byte_string):
    hasher = hashlib.sha256()
    hasher.update(byte_string)
    return hasher.digest()


def create_thing_storage():
    global SQLThingStorage

    class SQLThingStorage(actions.packaging.ThingStorage):
        def get_data(self, name):
            _logger.debug("getting", name)
            object = session.query(Thing).get(name)
            if object:
                data = object.thing_data
                return data
            else:
                object = session.query(Thing).get(name)
                if object:
                    data = object.thing_data
                    return data
                else:
                    return None

        def put_data(self, name, data):
            _logger.debug("putting", name, len(data))
            hash = sha512(data)
            object = session.query(Thing).get(name)
            if not object:
                _logger.debug("making", name)
                object = Thing(thing_key=name, owner_id=user.user_id, thing_data=data, thing_data_checksum=hash, encrypted=False)
                session.add(object)
            else:
                object.thing_data = data
                object.thing_data_checksum = hash
                object.encrypted = False

        def commit(self):
            _logger.debug("committing")
            session.commit()
