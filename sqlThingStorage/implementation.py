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
        primary_key=True)
    thing_key = sqlalchemy.Column(
        sqlalchemy.String(32),
        primary_key=True)
    target_id = sqlalchemy.Column(
        sqlalchemy.Integer(),
        sqlalchemy.ForeignKey('oa_users.user_id'),
        primary_key=True)
    permissions = sqlalchemy.Column(
        sqlalchemy.String(8),)
    owner = sqlalchemy.orm.relationship(
        "Thing",
        back_populates="user_permissions")
    __table_args__ = (
        sqlalchemy.ForeignKeyConstraint(
            (owner_id, thing_key),
            (Thing.owner_id, Thing.thing_key)),
        {
            "comment": "Open Assistant - Things' User Permissions"},
    )


def hash_password(password: str, salt: bytes) -> bytes:
    """
    Return a hashed password given a password and a salt.
    """
    pass_hash = sha512(password.encode("utf-8"))
    return hashlib.pbkdf2_hmac("sha512", pass_hash, salt, 100000)


def get_encryption_key(password: str, salt: bytes) -> bytes:
    """
    Return an encryption key given a password and a salt. This must be a raw password, not a password hash.
    """
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)


def sha512(byte_string: bytes) -> bytes:
    """
    Return a sha512 hash of a byte string. This is a pretty simple hashlib wrapper.
    """
    hasher = hashlib.sha512()
    hasher.update(byte_string)
    return hasher.digest()

def sha256(byte_string: bytes) -> bytes:
    """
    Return a sha256 hash of a byte string. This is a pretty simple hashlib wrapper.
    """
    hasher = hashlib.sha256()
    hasher.update(byte_string)
    return hasher.digest()


services = {}
plugin = {}
core = types.ModuleType
actions = types.ModuleType
root_user: User
user: User

valid_authentications = (
    AuthMethods.internal_password_00_01
)

def setup(engine):
    base.metadata.create_all(engine)
    with sqlalchemy.orm.Session(engine) as session:
        root_user = session.query(User).filter_by(user_name='/').first()
        if root_user is None:
            root_user = User(
                user_id=0,
                user_name="/",
                password_hash=b"\x00" * 64,
                password_salt=b"\x00" * 64,
                encryption_salt=b"\x00" * 64,
                auth_method=AuthMethods.internal_disabled,
                email="donotreply@donotreply.net")
            session.add(root_user)
            session.commit()
    return root_user
