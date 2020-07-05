import inspect
from re import (compile)
from .error import KiPlotConfigurationError
from . import log

logger = log.get_logger(__name__)


def filter(v):
    return inspect.isclass(v) or not (callable(v) or isinstance(v, (dict, list)))


class Optionable(object):
    """ A class to validate and hold configuration options.
        Is configured from a dict and the collected values are stored in its attributes. """
    _str_values_re = compile(r"\[string=.*\] \[([^\]]+)\]")
    _num_range_re = compile(r"\[number=.*\] \[(-?\d+),(-?\d+)\]")

    def __init__(self, name, description):
        super().__init__()
        self._name = name
        self._description = description
        self._unkown_is_error = True

    @staticmethod
    def _check_str(key, val, doc):
        if not isinstance(val, str):
            raise KiPlotConfigurationError("Option `{}` must be a string".format(key))
        # If the docstring specifies the allowed values in the form [v1,v2...] enforce it
        m = Optionable._str_values_re.match(doc)
        if m:
            vals = m.group(1).split(',')
            if val not in vals:
                raise KiPlotConfigurationError("Option `{}` must be any of {} not `{}`".format(key, vals, val))

    @staticmethod
    def _check_num(key, val, doc):
        if not isinstance(val, (int, float)):
            raise KiPlotConfigurationError("Option `{}` must be a number".format(key))
        # If the docstring specifies a range in the form [from-to] enforce it
        m = Optionable._num_range_re.match(doc)
        if m:
            min = float(m.group(1))
            max = float(m.group(2))
            if val < min or val > max:
                raise KiPlotConfigurationError("Option `{}` outside its range [{},{}]".format(key, min, max))

    @staticmethod
    def _check_bool(key, val):
        if not isinstance(val, bool):
            raise KiPlotConfigurationError("Option `{}` must be true/false".format(key))

    @staticmethod
    def _typeof(v):
        if isinstance(v, bool):
            return 'boolean'
        if isinstance(v, (int, float)):
            return 'number'
        if isinstance(v, str):
            return 'string'
        if isinstance(v, dict):
            return 'dict'
        if isinstance(v, list):
            return 'list'
        return 'None'

    def _perform_config_mapping(self):
        """ Map the options to class attributes """
        attrs = Optionable.get_attrs_for(self)
        for k, v in self._options.items():
            # Map known attributes and avoid mapping private ones
            if (k[0] == '_') or (k not in attrs):
                if self._unkown_is_error:
                    raise KiPlotConfigurationError("Unknown option `{}`".format(k))
                logger.warning("Unknown option `{}`".format(k))
                continue
            # Check the data type
            cur_val = getattr(self, k)
            cur_doc = getattr(self, '_help_'+k).lstrip()
            if isinstance(cur_val, bool):
                Optionable._check_bool(k, v)
            elif isinstance(cur_val, (int, float)):
                Optionable._check_num(k, v, cur_doc)
            elif isinstance(cur_val, str):
                Optionable._check_str(k, v, cur_doc)
            elif isinstance(cur_val, type):
                # A class, so we need more information i.e. "[dict|string]"
                if cur_doc[0] == '[':
                    # Separate the valid types for this key
                    valid = cur_doc[1:].split(']')[0].split('|')
                    # Get the type used by the user as a string
                    v_type = Optionable._typeof(v)
                    if v_type not in valid:
                        # Not a valid type for this key
                        if v_type == 'None':
                            raise KiPlotConfigurationError("Empty option `{}`".format(k))
                        raise KiPlotConfigurationError("Option `{}` must be any of {} not `{}`".format(k, valid, v_type))
                    # We know the type matches, now apply validations
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        # Note: booleans are also instance of int
                        Optionable._check_num(k, v, cur_doc)
                    elif isinstance(v, str):
                        Optionable._check_str(k, v, cur_doc)
                    elif isinstance(v, dict):
                        # Dicts are solved using Optionable classes
                        new_val = v
                        # Create an object for the valid class
                        v = cur_val(k, cur_doc)
                        # Delegate the validation to the object
                        v.config(new_val)
            # Seems to be ok, map it
            setattr(self, k, v)

    def config(self, options):
        self._options = options
        if options:
            self._perform_config_mapping()

    @staticmethod
    def get_attrs_for(obj):
        """ Returns all attributes """
        return dict(inspect.getmembers(obj, filter))

    @staticmethod
    def get_attrs_gen(obj):
        """ Returns a (key, val) iterator on public attributes """
        attrs = Optionable.get_attrs_for(obj)
        return ((k, v) for k, v in attrs.items() if k[0] != '_')
