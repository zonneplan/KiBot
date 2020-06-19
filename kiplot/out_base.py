import inspect
from .error import KiPlotConfigurationError
from . import log

logger = log.get_logger(__name__)


def filter(v):
    return not (callable(v) or inspect.isclass(v) or isinstance(v, (dict, list)))


class BaseOutput(object):
    _registered = {}

    def __init__(self, name, type, description):
        self._name = name
        self._type = type
        self._description = description
        self._sch_related = False

    def _perform_config_mapping(self):
        """ Map the options to class attributes """
        attrs = dict(inspect.getmembers(self, filter))
        for k, v in self._options.items():
            # Map known attributes and avoid mapping private ones
            if (k[0] == '_') or (k not in attrs):
                #  raise KiPlotConfigurationError("Unknown option `{}` {}".format(k, attrs))
                logger.warning("Unknown option `{}`".format(k))
                continue
            # Check the data type
            cur_val = self.__getattribute__(k)
            if isinstance(cur_val, bool) and not isinstance(v, bool):
                raise KiPlotConfigurationError("Option `{}` must be true/false".format(k))
            if isinstance(cur_val, (int, float)) and not isinstance(v, (int, float)):
                raise KiPlotConfigurationError("Option `{}` must be a number".format(k))
            if isinstance(cur_val, str) and not isinstance(v, str):
                raise KiPlotConfigurationError("Option `{}` must be a string".format(k))
            if isinstance(v, list):
                raise KiPlotConfigurationError("list not yet supported for `{}`".format(k))
            # Seems to be ok, map it
            setattr(self, k, v)

    def config(self, outdir, options, layers):
        self._outdir = outdir
        self._options = options
        self._layers = layers
        if options:
            self._perform_config_mapping()

    @staticmethod
    def register(name, aclass):
        BaseOutput._registered[name] = aclass

    @staticmethod
    def is_registered(name):
        return name in BaseOutput._registered

    @staticmethod
    def get_class_for(name):
        return BaseOutput._registered[name]

    def __str__(self):
        return "'{}' ({}) [{}]".format(self._description, self._name, self._type)

    def is_sch(self):
        """ True for outputs that works on the schematic """
        return self._sch_related

    def is_pcb(self):
        """ True for outputs that works on the PCB """
        return not self._sch_related

    # These get_* aren't really needed.
    # _* members aren't supposed to be used by the user, not the code.
    def get_name(self):
        return self._name

    def get_outdir(self):
        return self._outdir

    def run(self, output_dir, board):  # pragma: no cover
        logger.error("The run member for the class for the output type `{}` isn't implemented".format(self._type))
