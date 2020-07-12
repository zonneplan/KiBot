import os
import re
import inspect
from re import compile
from datetime import datetime
from .error import KiPlotConfigurationError
from .gs import GS
from . import log

logger = log.get_logger(__name__)


def filter(v):
    return inspect.isclass(v) or not (callable(v) or isinstance(v, (dict, list)))


class Optionable(object):
    """ A class to validate and hold configuration outputs/options.
        Is configured from a dict and the collected values are stored in its attributes. """
    _str_values_re = compile(r"\[string=.*\] \[([^\]]+)\]")
    _num_range_re = compile(r"\[number=.*\] \[(-?\d+),(-?\d+)\]")

    def __init__(self):
        super().__init__()
        self._unkown_is_error = False

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

    def get_doc(self, name):
        doc = getattr(self, '_help_'+name).strip()
        if doc[0] == '{':
            alias = doc[1:-1]
            return getattr(self, '_help_'+alias).strip(), alias, True
        return doc, name, False

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
            return 'list({})'.format(Optionable._typeof(v[0]))
        return 'None'

    def _perform_config_mapping(self):
        """ Map the options to class attributes """
        attrs = self.get_attrs_for()
        for k, v in self._tree.items():
            # Map known attributes and avoid mapping private ones
            if (k[0] == '_') or (k not in attrs):
                if self._unkown_is_error:
                    raise KiPlotConfigurationError("Unknown option `{}`".format(k))
                logger.warning("Unknown option `{}`".format(k))
                continue
            # Check the data type
            cur_doc, alias, is_alias = self.get_doc(k)
            cur_val = getattr(self, alias)
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
                        # Not used yet
                        Optionable._check_num(k, v, cur_doc)  # pragma: no cover
                    elif isinstance(v, str):
                        Optionable._check_str(k, v, cur_doc)
                    elif isinstance(v, dict):
                        # Dicts are solved using Optionable classes
                        new_val = v
                        # Create an object for the valid class
                        v = cur_val()
                        # Delegate the validation to the object
                        v.config(new_val)
                    elif isinstance(v, list):
                        new_val = []
                        for element in v:
                            e_type = 'list('+Optionable._typeof(element)+')'
                            if e_type not in valid:
                                raise KiPlotConfigurationError("Option `{}` must be any of {} not `{}`".
                                                               format(element, valid, e_type))
                            if isinstance(element, dict):
                                nv = cur_val()
                                nv.config(element)
                                new_val.append(nv)
                            else:
                                new_val.append(element)
                        v = new_val
            # Seems to be ok, map it
            setattr(self, alias if is_alias else k, v)

    def config(self, tree):
        self._tree = tree
        if tree:
            self._perform_config_mapping()

    def get_attrs_for(self):
        """ Returns all attributes """
        return dict(inspect.getmembers(self, filter))

    def get_attrs_gen(self):
        """ Returns a (key, val) iterator on public attributes """
        attrs = self.get_attrs_for()
        return ((k, v) for k, v in attrs.items() if k[0] != '_')

    def expand_filename(self, name, id='', ext=''):
        """ Expands %x values in filenames """
        if GS.board:
            # This is based on InterativeHtmlBom expansion
            title_block = GS.board.GetTitleBlock()
            file_date = title_block.GetDate()
            if not file_date:
                file_mtime = os.path.getmtime(GS.pcb_file)
                file_date = datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d_%H-%M-%S')
            pcb_file_name = os.path.splitext(os.path.basename(GS.pcb_file))[0]
            title = title_block.GetTitle()
            if not title:
                title = pcb_file_name
            revision = title_block.GetRevision()
            company = title_block.GetCompany()
            n = datetime.now()
            today = n.strftime('%Y-%m-%d')
            time = n.strftime('%H-%M-%S')
            # Do the replacements
            name = name.replace('%f', pcb_file_name)
            name = name.replace('%p', title)
            name = name.replace('%c', company)
            name = name.replace('%r', revision)
            name = name.replace('%d', file_date)
            name = name.replace('%D', today)
            name = name.replace('%T', time)
            name = name.replace('%i', id)
            name = name.replace('%x', ext)
            # sanitize the name to avoid characters illegal in file systems
            name = name.replace('\\', '/')
            name = re.sub(r'[?%*:|"<>]', '_', name)
        return name


class BaseOptions(Optionable):
    """ A class to validate and hold output options.
        Is configured from a dict and the collected values are stored in its attributes. """
    def __init__(self):
        super().__init__()

    def read_vals_from_po(self, po):
        """ Set attributes from a PCB_PLOT_PARAMS (plot options) """
        return
