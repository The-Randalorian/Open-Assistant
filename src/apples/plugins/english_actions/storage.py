import contextlib
import logging
# from concurrent.futures import ThreadPoolExecutor
import typing
import zlib

from camel import CamelRegistry, Camel

_logger = logging.getLogger(__name__)
# Used for debugging, assigns an incrementing number to
__load_counter = 0
# Limits the load counter on certain devices like servers where the number might become impossibly large
__load_counter_cap = 65535

thing_camel_registry = CamelRegistry()
misc_camel_registry = CamelRegistry()
camel_registries = (thing_camel_registry, misc_camel_registry)
thing_storage = []

dumper = thing_camel_registry.dumper
loader = thing_camel_registry.loader
misc_dumper = misc_camel_registry.dumper
misc_loader = misc_camel_registry.loader

general_knowledge = {}


def dump_raw(thing):
    raw = Camel(camel_registries).dump(thing)
    return raw


def dump(thing):
    _logger.debug("Dumping %s.", thing.name)
    raw = dump_raw(thing).encode("utf-8")
    _logger.debug("Dumped %s to %s bytes.", thing.name, len(raw))
    _logger.debug("Compressing dumped %s.", thing.name)
    data = zlib.compress(raw, level=9)
    _logger.debug("Compressed dumped %s to %s bytes.", thing.name, len(data))
    return data


def load_raw(raw):
    thing = Camel(camel_registries).load(raw)
    return thing


def load(data):
    global __load_counter
    log_id = __load_counter
    __load_counter = (__load_counter + 1) % __load_counter_cap
    _logger.debug("Decompressing unidentified object id:%s of %s bytes.", log_id, len(data))
    raw = zlib.decompress(data)
    _logger.debug("Decompressed unidentified object id:%s.", log_id)
    _logger.debug("Loading unidentified object id:%s of length %s bytes.", log_id, len(raw))
    thing = load_raw(raw.decode("utf-8"))
    _logger.debug(f"Loaded object id:{log_id}. Identified as {thing.name} of type {type(thing)}.")
    return thing


class ThingStorage:
    """
    A base class used for creating custom thing storage interfaces. This class is in charge of creating thing storage
    sessions for interaction with storage systems.

    A bare minimum implementation will implement the start_session method to create a thing storage session with
    appropriate parameters. For example, it might create a session with the appropriate login information for a certain
    user. Advanced implementations may implement the close_session, which takes a session as a parameter to close it.
    """

    thing_data = {}

    @contextlib.contextmanager
    def get_session(self):
        session = self.start_session()
        try:
            yield session
        finally:
            self.close_session(session)

    def start_session(self):
        """
        Start a session to interact with a storage system.
        """
        return ThingStorageSession(self)

    def close_session(self, session):
        """
        Close the active session.
        """
        pass


class ThingStorageSession:
    """
    A base class to use for making custom thing storage sessions. This class is normally not instantiated directly, and
    is instead created by a thing storage's start_session. The ThingStorage implementation is in charge of making sure
    the session is ready for use.

    A bare minimum implementation will implement the get_data, put_data, and delete_data methods. These directly load
    and store the raw binary data. Advanced implementations may also implement the commit_data method, which will force
    any cached data to be stored. The other functions, such as put, get and commit do not normally need to be changed.
    Only do so if absolutely necessary.

    It is very possible that put_data and get_data will be called with the same input parameters. Results are not
    cached in any way by open assistant. It is up to the implementer to create a caching system if one is desired. This
    is because the rest of Open Assistant has no knowledge of when the cache will go stale.

    Typically, a Thing Storage Session will have get and put called multiple times before commit is called. Normally
    after commit is called, the thing storage is destroyed, however this is not guaranteed. Implementers should make
    sure calls to put and get will still work after a commit.
    """
    def __init__(self, master: ThingStorage):
        self.master = master

    def get(self, name, default=None):
        """
        Load a Thing object from the data source and return the thing object.
        """
        data = self.get_data(name)
        if data is None:
            return default
        thing = load(data)
        self.add_to_session(thing)
        # Explicitly set __dict__["session"] to this object. This is important for thing references
        return thing

    def get_data(self, name: str):
        """
        Load a Thing object from the data source and return the raw binary data.
        """
        return self.master.thing_data.get(name, None)

    def put(self, thing, name: typing.Optional[str] = None):
        """
        Save thing data to the data source under a given name.

        Setting the name to None (Default) will save it as the thing's name.
        """
        if name is None:
            name = thing.name
        self.put_data(name, dump(thing))

    def put_data(self, name, data):
        """
        Save thing data to the data source under a given name.
        """
        self.master.thing_data[name] = data

    def delete(self, name: str):
        """
        Delete thing data on the data source under a given name.
        """
        self.delete_data(name)

    def delete_data(self, name: str):
        """
        Commit all data transactions. This should return when all the data is finalized.
        """
        del self.master.thing_data[name]

    def commit(self):
        """
        Commit all thing transactions. This should return when all the data is finalized.
        """
        self.commit_data()

    def commit_data(self):
        """
        Commit all data transactions. This should return when all the data is finalized.
        """
        pass
    
    def add_to_session(self, thing):
        if thing is not None:
            thing.__dict__["session"] = self
            thing.get_ref().session = self


class OptimizedThingStorage(ThingStorage):
    """
    A base class used for creating custom thing storage interfaces. This class acts similarly to a standard ThingStorage
    however it employs some built in optimizations.

    This class can also be subclassed if you want to use these same optimizations.
    """

    thing_data = {}
    static_thing_data = {}

    @contextlib.contextmanager
    def get_session(self):
        session = self.start_session()
        try:
            yield session
        finally:
            self.close_session(session)

    def start_session(self):
        """
        Start a session to interact with a storage system.
        """
        return OptimizedThingStorageSession(self)

    def close_session(self, session):
        """
        Close the active session.
        """
        pass


class OptimizedThingStorageSession(ThingStorageSession):
    """
    A base class to use for making custom thing storage sessions. This class acts similar to a standard
    ThingStorageSession, however it employs some built in optimizations. These optimizations work by selectively loading
    and saving data, instead of the shotgun "load and save EVERYTHING" approach of the base class. These optimizations
    may not be the best for every implementation however, so this class is kept separate from the base class.

    This class can also be subclassed if you want to use these same optimizations. The optimizations are almost entirely
    in the get, put, delete, and commit methods, instead of their _data equivalents. You can therefore modify the _data
    functions without worrying about messing up the optimizations. You WILL need to call super().__init__(master) in
    your implementation of __init__.
    """
    cache_only = {  # Save these things to the session cache, but NOT the main thing dictionary
                  "we",
                  "us",
                  "she",
                  "her",
                  "he",
                  "him",
                  "it",
                  "they",
                  "them",
                  "who"}

    def __init__(self, master: ThingStorage):
        super().__init__(master)
        self.cache = {}

    def get(self, name, default=None):
        """
        Load a Thing object from the data source and return the thing object.
        """
        cached_thing = self.cache.get(name, None)
        if cached_thing is not None:
            return cached_thing
        thing = super().get(name=name, default=default)
        if thing is not None:
            return thing
        thing = general_knowledge.get(name, None)
        if thing is not None:
            self.add_to_session(thing)
        return thing

    '''def get_data(self, name: str):
        """
        Load a Thing object from the data source and return the raw binary data.
        """
        return ThingStorage.thing_data.get(name, None)'''

    def put(self, thing, name: typing.Optional[str] = None):
        """
        Save thing data to the data source under a given name.

        Setting the name to None (Default) will save it as the thing's name.
        """
        if name is None:
            name = thing.name
        self.cache[name] = thing
        if name not in self.cache_only:
            super().put(thing=thing, name=name)

    '''def put_data(self, name, data):
        """
        Save thing data to the data source under a given name.
        """
        ThingStorage.thing_data[name] = data'''

    def delete(self, name: str):
        """
        Delete thing data on the data source under a given name.
        """
        self.cache.pop(name, None)
        super().delete(name)

    '''def delete_data(self, name: str):
        """
        Commit all data transactions. This should return when all the data is finalized.
        """
        del ThingStorage.thing_data[name]'''

    def commit(self):
        """
        Commit all thing transactions. This should return when all the data is finalized.
        """
        super().commit()

    '''def commit_data(self):
        """
        Commit all data transactions. This should return when all the data is finalized.
        """
        pass'''


_default_thing_storage = OptimizedThingStorage()


def get_default_storage() -> ThingStorage:
    _logger.debug(f"Using default thing storage {_default_thing_storage}.")
    return _default_thing_storage


def set_default_storage(storage: ThingStorage):
    global _default_thing_storage
    _default_thing_storage = storage
    _logger.debug(f"Set default thing storage to {_default_thing_storage}.")
