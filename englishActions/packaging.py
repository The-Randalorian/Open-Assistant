import contextlib
import sys, zlib, logging, collections
# from concurrent.futures import ThreadPoolExecutor

from camel import CamelRegistry, Camel

_logger = logging.getLogger("apples.englishActions." + __name__)
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
    _logger.debug("Loaded object id:#%s. Identified as %s.", log_id, thing.name)
    return thing


class ThingStorage:
    """
    A base class used for creating custom thing storage interfaces. This class is in charge of creating thing storage
    sessions for interaction with storage systems.

    A bare minimum implementation will implement the start_session method to create a thing storage session with
    appropriate parameters. For example, it might create a session with the appropriate login information for a certain
    user. Advanced implementations may implement the close_session, which takes a session as a parameter to close it.
    """
    def __init__(self):
        _things = {}

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
        return ThingStorageSession()

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

    A bare minimum implementation will implement the get_data and put_data methods. These directly load and store the
    raw binary data. Advanced implementations may also implement the commit_data method, which will force any cached
    data to be stored. The other functions, such as put, get and commit do not normally need to be changed. Only do so
    if absolutely necessary.

    It is very possible that put_data and get_data will be called with the same input parameters. Results are not
    cached in any way by open assistant. It is up to the implementer to create a caching system if one is desired. This
    is because the rest of Open Assistant has no knowledge of when the cache will go stale.

    Typically, a Thing Storage Session will have get and put called multiple times before commit is called. Normally
    after commit is called, the thing storage is destroyed, however this is not guaranteed. Implementers should make
    sure calls to put and get will still work after a commit.
    """
    def get(self, name):
        """
        Load a Thing object from the data source and return the thing object.
        """
        data = self.get_data(name)
        thing = load(data)
        return thing

    def get_data(self, name):
        """
        Load a Thing object from the data source and return the raw binary data.
        """
        pass

    def put(self, thing):
        """
        Save thing data to the data source under a given name.
        """
        self.put_data(thing.name, dump(thing))

    def put_data(self, name, data):
        """
        Save thing data to the data source under a given name.
        """
        pass

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