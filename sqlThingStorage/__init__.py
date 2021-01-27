import threading, time, logging, hashlib, os

from sqlalchemy import Column, Integer, String, LargeBinary, Boolean, ForeignKey, create_engine
from sqlalchemy.orm import backref, sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

base = declarative_base()

_logger = logging.getLogger(__name__)


'''class Group(base):
    __tablename__ = "groups"
    group_id = Column(Integer(), primary_key=True)
    group_name = Column(String(32), unique=True)
    owner_id = Column(Integer(), ForeignKey('users.user_id'))'''


class User(base):
    __tablename__ = 'users'
    user_id = Column(Integer(), primary_key=True)
    user_name = Column(String(32), unique=True)
    password_hash = Column(LargeBinary(64))
    password_salt = Column(LargeBinary(64))
    encryption_salt = Column(LargeBinary(64))
    email = Column(String(254))  # Apparently the maximum usable email address length, see https://7php.com/the-maximum-length-limit-of-an-email-address-is-254-not-320/#:~:text=there%20is%20a%20length%20limit,total%20length%20of%20320%20characters.

    things = backref("Thing", back_populates="owner")


class Thing(base):
    __tablename__ = 'things'
    thing_key = Column(String(255), primary_key=True)
    owner_id = Column(Integer(), ForeignKey('users.user_id'))
    thing_data = Column(LargeBinary(65535))
    thing_data_checksum = Column(LargeBinary(65535))
    encrypted = Column(Boolean())


services = {}
plugin = {}
core = None
actions = None
engine = None
session_maker = None
session_scope = None
session = None
root_user = None
user = None
encryption_key = b''*64
SQLThingStorage = object


def _register_(serviceList, pluginProperties):
    global services, plugin, core, actions, engine, session_maker, session_scope, session, root_user, user, encryption_key
    services = serviceList
    plugin = pluginProperties
    core = services["core"][0]
    actions = services["actions"][0]
    #core.addStart(startThread)
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
    engine = create_engine(
        database_url,
        echo=False)
    base.metadata.create_all(engine)
    session_maker = sessionmaker(bind=engine)
    #session_scope = scoped_session(sessionmaker)
    #session = session_scope()
    session = session_maker()
    root_user = session.query(User).filter_by(user_name='-').first()
    if root_user is None:
        root_user = User(
            user_id=0,
            user_name="-",
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
            object = session.query(Thing).get(f"{user.user_name}%{name}")
            if object:
                data = object.thing_data
                return data
            else:
                object = session.query(Thing).get(f"{root_user.user_name}%{name}")
                if object:
                    data = object.thing_data
                    return data
                else:
                    return None

        def put_data(self, name, data):
            _logger.debug("putting", name, len(data))
            hash = sha512(data)
            object = session.query(Thing).get(f"{user.user_name}%{name}")
            if not object:
                _logger.debug("making", name)
                object = Thing(thing_key=f"{user.user_name}%{name}", owner_id=user.user_id, thing_data=data, thing_data_checksum=hash, encrypted=False)
                session.add(object)
            else:
                object.thing_data = data
                object.thing_data_checksum = hash
                object.encrypted = False


        def commit(self):
            _logger.debug("committing")
            session.commit()


def loopTask():
    pass


def startThread():
    pass


def closeThread():
    pass
