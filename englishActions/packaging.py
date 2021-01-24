import sys, zlib, logging, collections
from concurrent.futures import ThreadPoolExecutor
from abc import abstractmethod, ABC

from camel import CamelRegistry, Camel

_logger = logging.getLogger("apples.englishActions." + __name__)

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

__load_counter = 0
def load(data):
    global __load_counter
    log_id = __load_counter
    __load_counter += 1
    _logger.debug("Decompressing unidentified object id:%s of %s bytes.", log_id, len(data))
    raw = zlib.decompress(data)
    _logger.debug("Decompressed unidentified object id:%s.", log_id)
    _logger.debug("Loading unidentified object id:%s of length %s bytes.", log_id, len(raw))
    thing = load_raw(raw.decode("utf-8"))
    _logger.debug("Loaded object id:#%s. Identified as %s.", log_id, thing.name)
    return thing


class ThingStorage(ABC):
    def __init__(self):
        self.executor = ThreadPoolExecutor()
        self.get_tasks = {}
        self.put_tasks = collections.deque()
        self.data = {}

    def pre_get(self, name, callback=None):
        self.get(name, callback)
        # self.get_tasks[name] = self._make_get_task(name, callback)

    def _make_get_task(self, name, callback):
        return self.executor.submit(self._get_wrapper, name, callback)

    def get(self, name, callback=None):
        task = self.get_tasks.get("name", self._make_get_task(name, callback))
        return task.result()

    def _get_wrapper(self, name, callback):
        data = self.get_data(name)
        if data is None:
            return None
        thing = load(data)
        if callback is not None:
            callback(thing)
        return thing

    @abstractmethod
    def get_data(self, name):
        # print("finding", name)
        # return self.data.get(name, None)
        return None

    def pull(self):
        for key in self.get_tasks.keys():
            self.get_tasks.pop(key).result()

    def _make_put_task(self, name, data, callback):
        return self.executor.submit(self._put_wrapper, name, data, callback)

    def put(self, thing, callback=None):
        #self.put_tasks.append(self._make_put_task(thing.name, dump(thing), callback))
        self._put_wrapper(thing.name, dump(thing), callback)

    def _put_wrapper(self, name, data, callback):
        self.put_data(name, data)
        if callback is not None:
            callback(name, data)
        #self.commit()

    @abstractmethod
    def put_data(self, name, data):
        # print("saving", name, data)
        # self.data[name] = data
        pass

    def push(self):
        for task in range(len(self.put_tasks)):
            _logger.debug(str(self.put_tasks[task].result()))
        self.commit()

    def commit(self):
        pass


def set_thing_storage(ts):
    global thing_storage
    thing_storage = [ts]


def get_thing_storage():
    try:
        return thing_storage[0]
    except IndexError:
        return None


def push():
    return get_thing_storage().push()


def commit():
    return get_thing_storage().commit()


def put(thing, callback=None):
    return get_thing_storage().put(thing, callback)


def get(name, callback=None):
    return get_thing_storage().get(name, callback)


def pre_get(name, callback=None):
    return get_thing_storage().pre_get(name, callback)
