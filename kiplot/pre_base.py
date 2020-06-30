from .gs import (GS)
from .log import (get_logger)

logger = get_logger(__name__)


class BasePreFlight(object):
    _registered = {}
    _in_use = {}
    _options = {}

    def __init__(self, name, value):
        self._value = value
        self._name = name
        self._sch_related = False
        self._pcb_related = False
        self._enabled = True

    @staticmethod
    def register(name, aclass):
        BasePreFlight._registered[name] = aclass

    @staticmethod
    def is_registered(name):
        return name in BasePreFlight._registered

    @staticmethod
    def get_registered():
        return BasePreFlight._registered

    @staticmethod
    def get_class_for(name):
        return BasePreFlight._registered[name]

    @staticmethod
    def add_preflight(o_pre):
        BasePreFlight._in_use[o_pre._name] = o_pre

    @staticmethod
    def get_preflight(name):
        return BasePreFlight._in_use.get(name)

    @staticmethod
    def get_in_use_objs():
        return BasePreFlight._in_use.values()

    @staticmethod
    def _set_option(name, value):
        BasePreFlight._options[name] = value

    @staticmethod
    def get_option(name):
        return BasePreFlight._options.get(name)

    @staticmethod
    def run_enabled():
        for k, v in BasePreFlight._in_use.items():
            if v._enabled:
                if v.is_sch():
                    GS.check_sch()
                if v.is_pcb():
                    GS.check_pcb()
                logger.debug('Preflight apply '+k)
                v.apply()
        for k, v in BasePreFlight._in_use.items():
            if v._enabled:
                logger.debug('Preflight run '+k)
                v.run()

    def disable(self):
        self._enabled = False

    def is_enabled(self):
        return self._enabled

    def __str__(self):
        return "{}: {}".format(self._name, self._enabled)

    def is_sch(self):
        """ True for preflights that needs the schematic """
        return self._sch_related

    def is_pcb(self):
        """ True for preflights that needs the PCB """
        return self._pcb_related

    def get_example():
        """ Returns a YAML value for the example config """
        return 'true'

    def run(self, brd_file):  # pragma: no cover
        logger.error("The run method for the preflight class name `{}` isn't implemented".format(self._name))

    def apply(self, brd_file):  # pragma: no cover
        logger.error("The apply method for the preflight class  name `{}` isn't implemented".format(self._name))
