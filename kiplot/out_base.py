import inspect
from re import (compile)
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
        attrs = BaseOutput.get_attrs_for(self)
        num_range_re = compile(r"\[number=.*\] \[(-?\d+),(-?\d+)\]")
        str_values_re = compile(r"\[string=.*\] \[([^\]]+)\]")
        for k, v in self._options.items():
            # Map known attributes and avoid mapping private ones
            if (k[0] == '_') or (k not in attrs):
                #  raise KiPlotConfigurationError("Unknown option `{}` {}".format(k, attrs))
                logger.warning("Unknown option `{}`".format(k))
                continue
            # Check the data type
            cur_val = getattr(self, k)
            cur_doc = getattr(self, '_help_'+k).lstrip()
            if isinstance(cur_val, bool):
                if not isinstance(v, bool):
                    raise KiPlotConfigurationError("Option `{}` must be true/false".format(k))
            elif isinstance(cur_val, (int, float)):
                # Note: booleans are also instance of int
                if not isinstance(v, (int, float)):
                    raise KiPlotConfigurationError("Option `{}` must be a number".format(k))
                # If the docstring specifies a range in the form [from-to] enforce it
                m = num_range_re.match(cur_doc)
                if m:
                    min = float(m.group(1))
                    max = float(m.group(2))
                    if v < min or v > max:
                        raise KiPlotConfigurationError("Option `{}` outside its range [{},{}]".format(k, min, max))
            elif isinstance(cur_val, str):
                if not isinstance(v, str):
                    raise KiPlotConfigurationError("Option `{}` must be a string".format(k))
                # If the docstring specifies the allowed values in the form [v1,v2...] enforce it
                m = str_values_re.match(cur_doc)
                if m:
                    vals = m.group(1).split(',')
                    if v not in vals:
                        raise KiPlotConfigurationError("Option `{}` must be any of {}".format(k, vals))
            elif isinstance(v, list):
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
    def get_attrs_for(obj):
        """ Returns all attributes """
        return dict(inspect.getmembers(obj, filter))

    @staticmethod
    def get_attrs_gen(obj):
        """ Returns a (key, val) iterator on public attributes """
        attrs = BaseOutput.get_attrs_for(obj)
        return ((k, v) for k, v in attrs.items() if k[0] != '_')

    @staticmethod
    def attr2longopt(attr):
        return '--'+attr.replace('_', '-')

    @staticmethod
    def register(name, aclass):
        BaseOutput._registered[name] = aclass

    @staticmethod
    def is_registered(name):
        return name in BaseOutput._registered

    @staticmethod
    def get_class_for(name):
        return BaseOutput._registered[name]

    @staticmethod
    def get_registered():
        return BaseOutput._registered

    def __str__(self):
        return "'{}' ({}) [{}]".format(self._description, self._name, self._type)

    def is_sch(self):
        """ True for outputs that works on the schematic """
        return self._sch_related

    def is_pcb(self):
        """ True for outputs that works on the PCB """
        return not self._sch_related

    def read_vals_from_po(self, po):
        """ Set attributes from a PCB_PLOT_PARAMS (plot options) """
        return

    # These get_* aren't really needed.
    # _* members aren't supposed to be used by the user, not the code.
    def get_name(self):
        return self._name

    def get_outdir(self):
        return self._outdir

    def run(self, output_dir, board):  # pragma: no cover
        logger.error("The run member for the class for the output type `{}` isn't implemented".format(self._type))
