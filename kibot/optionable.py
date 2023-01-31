# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
""" Base class for output options """
import difflib
import inspect
import os
import re
from re import compile
from .error import KiPlotConfigurationError
from .gs import GS
from .misc import W_UNKOPS, DISTRIBUTORS_STUBS, DISTRIBUTORS_STUBS_SEPS
from . import log

logger = log.get_logger()
HEX_DIGIT = '[A-Fa-f0-9]{2}'
INVALID_CHARS = r'[?%*:|"<>]'
PATTERNS_DEP = ['%c', '%d', '%F', '%f', '%p', '%r']
for n in range(1, 10):
    PATTERNS_DEP.append('%C'+str(n))


def do_filter(v):
    return inspect.isclass(v) or not (callable(v) or isinstance(v, (dict, list)))


def _cl(text):
    """ Eliminates dangerous characters from the text """
    return re.sub(r'[\\\/\?%\*:|"<>]', '_', text)


class Optionable(object):
    """ A class to validate and hold configuration outputs/options.
        Is configured from a dict and the collected values are stored in its attributes. """
    _str_values_re = compile(r"string=.*\] \[([^\]]+)\]")
    _num_range_re = compile(r"number=.*\] \[(-?\d+),(-?\d+)\]")
    _default = None

    _color_re = re.compile(r"#("+HEX_DIGIT+"){3}$")
    _color_re_a = re.compile(r"#("+HEX_DIGIT+"){4}$")
    _color_re_component = re.compile(HEX_DIGIT)

    def __init__(self):
        self._unkown_is_error = False
        self._error_context = ''
        self._tree = {}
        self._configured = False
        # File/directory pattern expansion
        self._expand_id = ''
        self._expand_ext = ''
        # Used to indicate we have an output pattern and it must be suitable to generate multiple files
        self._output_multiple_files = False
        # The KiBoM output uses "variant" for the KiBoM variant, not for KiBot variants
        self._variant_is_real = True
        super().__init__()
        for var in ['output', 'variant', 'units', 'hide_excluded']:
            glb = getattr(GS, 'global_'+var)
            if glb and hasattr(self, var):
                setattr(self, var, glb)
                if GS.debug_level > 2:
                    logger.debug('Using global `{}`=`{}`'.format(var, glb))

    @staticmethod
    def _check_str(key, val, doc):
        if not isinstance(val, str):
            raise KiPlotConfigurationError("Option `{}` must be a string".format(key))
        # If the docstring specifies the allowed values in the form [v1,v2...] enforce it
        m = Optionable._str_values_re.search(doc)
        if m:
            vals = m.group(1).split(',')
            if val not in vals:
                raise KiPlotConfigurationError("Option `{}` must be any of {} not `{}`".format(key, vals, val))

    @staticmethod
    def _check_num(key, val, doc):
        if not isinstance(val, (int, float)):
            raise KiPlotConfigurationError("Option `{}` must be a number".format(key))
        # If the docstring specifies a range in the form [from-to] enforce it
        m = Optionable._num_range_re.search(doc)
        if m:
            min = float(m.group(1))
            max = float(m.group(2))
            if val < min or val > max:
                raise KiPlotConfigurationError("Option `{}` outside its range [{},{}]".format(key, min, max))

    @staticmethod
    def _check_bool(key, val):
        if not isinstance(val, bool):
            raise KiPlotConfigurationError("Option `{}` must be true/false".format(key))

    def get_doc(self, name, no_basic=False):
        try:
            doc = getattr(self, '_help_'+name).strip()
        except AttributeError:
            return None, name, False
        if doc[0] == '{':
            alias = doc[1:-1]
            return getattr(self, '_help_'+alias).strip(), alias, True
        if no_basic and doc[0] == '*':
            # Remove the 'basic' indicator
            doc = doc[1:]
        return doc, name, False

    def is_basic_option(self, name):
        help, _, _ = self.get_doc(name)
        return help and help[0] == '*'

    def add_to_doc(self, name, text):
        doc = getattr(self, '_help_'+name).strip()
        setattr(self, '_help_'+name, doc+'.\n'+text)

    def set_doc(self, name, text):
        setattr(self, '_help_'+name, text)

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
            if len(v) == 0:
                return 'list(string)'
            return 'list({})'.format(Optionable._typeof(v[0]))
        return 'None'

    def _perform_config_mapping(self):
        """ Map the options to class attributes """
        attrs = self.get_attrs_for()
        if not isinstance(self._tree, dict):
            raise KiPlotConfigurationError('Found {} instead of dict'.format(type(self._tree)))
        for k, v in self._tree.items():
            # Map known attributes and avoid mapping private ones
            if (k[0] == '_') or (k not in attrs):
                if self._unkown_is_error:
                    valid = list(filter(lambda x: x[0] != '_', attrs.keys()))
                    msg = "Unknown {}option `{}`.".format(self._error_context, k)
                    possible = difflib.get_close_matches(k, valid, n=1)
                    if possible:
                        msg += " Did you meen {}?".format(possible[0])
                    msg += " Valid options: {}".format(valid)
                    raise KiPlotConfigurationError(msg)
                logger.warning(W_UNKOPS + "Unknown {}option `{}`".format(self._error_context, k))
                continue
            # Check the data type
            cur_doc, alias, is_alias = self.get_doc(k, no_basic=True)
            cur_val = getattr(self, alias)
            if cur_doc[0] == '[':
                # Separate the valid types for this key
                valid = cur_doc[1:].split(']')[0].split('|')
                # Remove the XXXX=Value
                if '=' in valid[-1]:
                    valid[-1] = valid[-1].split('=')[0]
                # Get the type used by the user as a string
                v_type = Optionable._typeof(v)
                if v_type not in valid:
                    # Not a valid type for this key
                    if v_type == 'None':
                        raise KiPlotConfigurationError("Empty option `{}`".format(k))
                    if len(valid) == 1:
                        raise KiPlotConfigurationError("Option `{}` must be a {} not `{}`".format(k, valid[0], v_type))
                    else:
                        raise KiPlotConfigurationError("Option `{}` must be any of {} not `{}`".format(k, valid, v_type))
            else:
                valid = None
                v_type = Optionable._typeof(cur_val)
            if v_type == 'boolean':
                Optionable._check_bool(k, v)
            elif v_type == 'number':
                Optionable._check_num(k, v, cur_doc)
            elif v_type == 'string':
                Optionable._check_str(k, v, cur_doc)
            elif isinstance(cur_val, type):
                # A class, so we need more information i.e. "[dict|string]"
                if valid is not None:
                    # We know the type matches, now apply validations
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        # Note: booleans are also instance of int
                        # Not used yet
                        Optionable._check_num(k, v, cur_doc)  # pragma: no cover (Internal)
                    elif isinstance(v, str):
                        Optionable._check_str(k, v, cur_doc)
                    elif isinstance(v, dict):
                        # Dicts are solved using Optionable classes
                        new_val = v
                        # Create an object for the valid class
                        v = cur_val()
                        # Delegate the validation to the object
                        v.set_tree(new_val)
                        v.config(self)
                    elif isinstance(v, list):
                        new_val = []
                        for element in v:
                            e_type = 'list('+Optionable._typeof(element)+')'
                            if e_type not in valid:
                                raise KiPlotConfigurationError("Option `{}` must be any of {} not `{}`".
                                                               format(element, valid, e_type))
                            if isinstance(element, dict):
                                nv = cur_val()
                                nv.set_tree(element)
                                nv.config(self)
                                new_val.append(nv)
                            else:
                                new_val.append(element)
                        v = new_val
            # Seems to be ok, map it
            dest_name = alias if is_alias else k
            setattr(self, dest_name, v)
            self.set_user_defined(dest_name)

    def set_user_defined(self, name):
        setattr(self, '_{}_user_defined'.format(name), True)

    def get_user_defined(self, name):
        name = '_{}_user_defined'.format(name)
        if hasattr(self, name):
            return getattr(self, name)
        return False

    def set_tree(self, tree):
        self._tree = tree

    def config(self, parent):
        self._parent = parent
        if self._tree and not self._configured:
            self._perform_config_mapping()
            self._configured = True
        if self._output_multiple_files and ('%i' not in self.output or '%x' not in self.output):
            raise KiPlotConfigurationError('The output pattern must contain %i and %x, otherwise file names will collide')

    def get_attrs_for(self):
        """ Returns all attributes """
        return dict(inspect.getmembers(self, do_filter))

    def get_attrs_gen(self):
        """ Returns a (key, val) iterator on public attributes """
        attrs = self.get_attrs_for()
        return ((k, v) for k, v in attrs.items() if k[0] != '_')

    @staticmethod
    def _find_global_variant():
        if GS.solved_global_variant:
            return GS.solved_global_variant.file_id
        return ''

    def _find_variant(self):
        """ Returns the text to add for the current variant.
            Also try with the globally defined variant.
            If no variant is defined an empty string is returned. """
        if not self._variant_is_real:
            return self.variant
        if hasattr(self, 'variant') and self.variant:
            self.variant = GS.solve_variant(self.variant)
            return self.variant.file_id
        return Optionable._find_global_variant()

    @staticmethod
    def _find_global_variant_name():
        if GS.solved_global_variant:
            return GS.solved_global_variant.name
        return ''

    def _find_variant_name(self):
        """ Returns the name for the current variant.
            Also try with the globally defined variant.
            If no variant is defined an empty string is returned. """
        if not self._variant_is_real:
            return self.variant
        if hasattr(self, 'variant') and self.variant:
            self.variant = GS.solve_variant(self.variant)
            return self.variant.name
        return Optionable._find_global_variant_name()

    @staticmethod
    def _find_global_subpcb():
        if GS.solved_global_variant and GS.solved_global_variant._sub_pcb:
            return GS.solved_global_variant._sub_pcb.name
        return ''

    def _find_subpcb(self):
        """ Returns the name of the sub-PCB.
            Also try with the globally defined variant.
            If no variant is defined an empty string is returned. """
        if not self._variant_is_real:
            return ''
        if hasattr(self, 'variant') and self.variant:
            self.variant = GS.solve_variant(self.variant)
            if self.variant._sub_pcb:
                return self.variant._sub_pcb.name
        return Optionable._find_global_subpcb()

    def expand_filename_common(self, name, parent):
        """ Expansions common to the PCB and Schematic """
        # PCB expansions, explicit
        if GS.board and '%b' in name:
            name = name.replace('%bc', _cl(GS.pcb_comp))
            name = name.replace('%bd', _cl(GS.pcb_date))
            name = name.replace('%bF', GS.pcb_no_ext)
            name = name.replace('%bf', GS.pcb_basename)
            name = name.replace('%bp', _cl(GS.pcb_title))
            name = name.replace('%br', _cl(GS.pcb_rev))
            for num, val in enumerate(GS.pcb_com):
                name = name.replace('%bC'+str(num+1), _cl(val))
        if GS.solved_global_variant:
            name = name.replace('%g', GS.solved_global_variant.file_id)
            name = name.replace('%G', GS.solved_global_variant.name)
        # Schematic expansions, explicit
        if GS.sch and '%s' in name:
            name = name.replace('%sc', _cl(GS.sch_comp))
            name = name.replace('%sd', _cl(GS.sch_date))
            name = name.replace('%sF', GS.sch_no_ext)
            name = name.replace('%sf', GS.sch_basename)
            name = name.replace('%sp', _cl(GS.sch_title))
            name = name.replace('%sr', _cl(GS.sch_rev))
            for num, val in enumerate(GS.sch_com):
                name = name.replace('%sC'+str(num+1), _cl(val))
        name = name.replace('%D', GS.n.strftime(GS.global_date_format))
        name = name.replace('%T', GS.n.strftime(GS.global_time_format))
        if self:
            name = name.replace('%i', self._expand_id)
            name = name.replace('%v', _cl(self._find_variant()))
            name = name.replace('%V', _cl(self._find_variant_name()))
            name = name.replace('%S', _cl(self._find_subpcb()))
            name = name.replace('%x', self._expand_ext)
            replace_id = ''
            if parent and hasattr(parent, 'output_id'):
                replace_id = _cl(parent.output_id)
            name = name.replace('%I', replace_id)
        else:
            name = name.replace('%v', _cl(Optionable._find_global_variant()))
            name = name.replace('%V', _cl(Optionable._find_global_variant_name()))
        return name

    def expand_filename_both(self, name, is_sch=True, make_safe=True):
        """ Expands %* values in filenames.
            Uses data from the PCB. """
        parent = None
        if self and hasattr(self, '_parent'):
            parent = self._parent
        if GS.debug_level > 3:
            logger.debug('Expanding `{}` in {} context for {} parent: {}'.
                         format(name, 'SCH' if is_sch else 'PCB', self, parent))
        # Replace KiCad 6 variables first
        name = GS.expand_text_variables(name)
        # Determine if we need to expand SCH and/or PCB related data
        has_dep_exp = any(map(lambda x: x in name, PATTERNS_DEP))
        do_sch = is_sch and has_dep_exp
        # logger.error(name + '  is_sch ' +str(is_sch)+"   "+ str(do_sch))
        # raise
        do_pcb = not is_sch and has_dep_exp
        # Load the needed data
        if GS.pcb_file and (do_pcb or '%b' in name):
            if GS.board is None:
                GS.load_board()
            GS.load_pcb_title_block()
        if GS.sch_file and (do_sch or '%s' in name):
            if GS.sch is None:
                GS.load_sch()
            GS.load_sch_title_block()
        # This member can be called with a preflight object
        name = Optionable.expand_filename_common(self, name, parent)
        if GS.board and do_pcb:
            name = name.replace('%c', _cl(GS.pcb_comp))
            name = name.replace('%d', _cl(GS.pcb_date))
            name = name.replace('%F', GS.pcb_no_ext)
            name = name.replace('%f', GS.pcb_basename)
            name = name.replace('%p', _cl(GS.pcb_title))
            name = name.replace('%r', _cl(GS.pcb_rev))
            for num, val in enumerate(GS.pcb_com):
                name = name.replace('%C'+str(num+1), _cl(val))
        if GS.sch and do_sch:
            name = name.replace('%c', _cl(GS.sch_comp))
            name = name.replace('%d', _cl(GS.sch_date))
            name = name.replace('%F', GS.sch_no_ext)
            name = name.replace('%f', GS.sch_basename)
            name = name.replace('%p', _cl(GS.sch_title))
            name = name.replace('%r', _cl(GS.sch_rev))
            for num, val in enumerate(GS.sch_com):
                name = name.replace('%C'+str(num+1), _cl(val))
        # Also replace KiCad 6 variables after it
        name = GS.expand_text_variables(name)
        if make_safe:
            # sanitize the name to avoid characters illegal in file systems
            if GS.on_windows:
                # Here \ *is* valid
                if len(name) >= 2 and name[0].isalpha() and name[1] == ':':
                    # This name starts with a drive letter, : is valid in the first 2
                    name = name[:2]+re.sub(INVALID_CHARS, '_', name[2:])
                else:
                    name = re.sub(INVALID_CHARS, '_', name)
            else:
                name = name.replace('\\', '/')
                name = re.sub(INVALID_CHARS, '_', name)
        if GS.debug_level > 3:
            logger.debug('Expanded `{}`'.format(name))
        return name

    def expand_filename_pcb(self, name):
        """ Expands %* values in filenames.
            Uses data from the PCB. """
        # This member can be called with a preflight object
        return Optionable.expand_filename_both(self, name, is_sch=False)

    def expand_filename_sch(self, name):
        """ Expands %* values in filenames.
            Uses data from the SCH. """
        # This member can be called with a preflight object
        return Optionable.expand_filename_both(self, name)

    @staticmethod
    def force_list(val, comma_sep=True, lower_case=False):
        """ Used for values that accept a string or a list of strings.
            The string can be a comma separated list """
        if isinstance(val, type):
            # Not used
            val = []
        elif isinstance(val, str):
            # A string
            if val:
                if comma_sep:
                    val = [v.strip() for v in val.split(',')]
                else:
                    val = [val]
            else:
                # Empty string
                val = []
        if lower_case:
            return [c.lower() for c in val]
        return val

    @classmethod
    def get_default(cls):
        return cls._default

    def validate_color_str(self, color):
        return self._color_re.match(color) or self._color_re_a.match(color)

    def validate_color(self, name):
        if not self.validate_color_str(getattr(self, name)):
            raise KiPlotConfigurationError('Invalid color for `{}` use `#rrggbb` or `#rrggbbaa` with hex digits'.format(name))

    def validate_colors(self, names):
        for color in names:
            self.validate_color(color)

    def parse_one_color(self, color):
        res = self._color_re_component.findall(color)
        alpha = 1.0
        if len(res) > 3:
            alpha = int(res[3], 16)/255.0
        return (int(res[0], 16)/255.0, int(res[1], 16)/255.0, int(res[2], 16)/255.0, alpha)

    def color_to_rgb(self, color):
        index = 4 if len(color) > 4 else 0
        alpha = color[index+3]
        if alpha == 1.0:
            return "rgb({}, {}, {})".format(round(color[index]*255.0), round(color[index+1]*255.0),
                                            round(color[index+2]*255.0))
        return "rgba({}, {}, {}, {})".format(round(color[index]*255.0), round(color[index+1]*255.0),
                                             round(color[index+2]*255.0), alpha)

    def color_str_to_rgb(self, color):
        return self.color_to_rgb(self.parse_one_color(color))

    @staticmethod
    def _solve_field_name(field, empty_when_none):
        """ Applies special replacements for field """
        # The global name for the LCSC part field
        if GS.global_field_lcsc_part:
            logger.debug('- User selected: '+GS.global_field_lcsc_part)
            return GS.global_field_lcsc_part
        # No name defined, try to figure out
        if not GS.sch and GS.sch_file:
            GS.load_sch()
        if not GS.sch:
            logger.debug("- No schematic loaded, can't search the name")
            return '' if empty_when_none else 'LCSC#'
        if hasattr(GS.sch, '_field_lcsc_part'):
            return GS.sch._field_lcsc_part
        # Look for a common name
        fields = {f.lower() for f in GS.sch.get_field_names([])}
        for stub in DISTRIBUTORS_STUBS:
            fld = 'lcsc'+stub
            if fld in fields:
                GS.sch._field_lcsc_part = fld
                return fld
            if stub != '#':
                for sep in DISTRIBUTORS_STUBS_SEPS:
                    fld = 'lcsc'+sep+stub
                    if fld in fields:
                        GS.sch._field_lcsc_part = fld
                        return fld
        if 'lcsc' in fields:
            GS.sch._field_lcsc_part = 'LCSC'
            return 'LCSC'
        # Look for a field that only contains LCSC codes
        comps = GS.sch.get_components()
        lcsc_re = re.compile(r'C\d+')
        for f in fields:
            found = False
            for c in comps:
                val = c.get_field_value(f).strip()
                if not val:
                    continue
                if lcsc_re.match(val):
                    found = True
                else:
                    found = False
                    break
            if found:
                GS.sch._field_lcsc_part = f
                return f
        logger.debug('- No LCSC field found')
        res = '' if empty_when_none else 'LCSC#'
        GS.sch._field_lcsc_part = res
        return res

    @staticmethod
    def solve_field_name(field, empty_when_none=False):
        if field != '_field_lcsc_part':
            return field
        logger.debug('Looking for LCSC field name')
        field = Optionable._solve_field_name(field, empty_when_none)
        logger.debug('Using {} as LCSC field name'.format(field))
        return field


class BaseOptions(Optionable):
    """ A class to validate and hold output options.
        Is configured from a dict and the collected values are stored in its attributes. """
    def __init__(self):
        super().__init__()

    def read_vals_from_po(self, po):
        """ Set attributes from a PCB_PLOT_PARAMS (plot options) """
        return

    def ensure_tool(self, name):
        """ Looks for a mandatory dependency """
        return GS.check_tool_dep(self._parent.type, name, fatal=True)

    def ensure_tool_get_ver(self, name):
        """ Looks for a mandatory dependency, also returns its version """
        return GS.check_tool_dep_get_ver(self._parent.type, name, fatal=True)

    def check_tool(self, name):
        """ Looks for a dependency """
        return GS.check_tool_dep(self._parent.type, name, fatal=False)

    def expand_filename(self, dir, name, id, ext, make_safe=True):
        cur_id = self._expand_id
        cur_ext = self._expand_ext
        self._expand_id = id
        self._expand_ext = ext
        name = self.expand_filename_both(name, is_sch=self._parent._sch_related, make_safe=make_safe)
        res = os.path.abspath(os.path.join(dir, name))
        self._expand_id = cur_id
        self._expand_ext = cur_ext
        return res


class PanelOptions(BaseOptions):
    """ A class for options that uses KiKit's units """
    _num_regex = re.compile(r'([\d\.]+)(mm|cm|dm|m|mil|inch|in)')
    _ang_regex = re.compile(r'([\d\.]+)(deg|°|rad)')

    def add_units(self, ops, def_units=None, convert=False):
        if def_units is None:
            def_units = self._parent._parent.units
        for op in ops:
            val = getattr(self, op)
            _op = '_'+op
            if val is None:
                if convert:
                    setattr(self, _op, 0)
                continue
            if isinstance(val, (int, float)):
                setattr(self, op, str(val)+def_units)
                if convert:
                    setattr(self, _op, val*GS.kikit_units_to_kicad[def_units])
            else:
                m = PanelOptions._num_regex.match(val)
                if m is None:
                    raise KiPlotConfigurationError('Malformed value `{}: {}` must be a number and units'.format(op, val))
                num = m.group(1)
                try:
                    num_d = float(num)
                except ValueError:
                    num_d = None
                if num_d is None:
                    raise KiPlotConfigurationError('Malformed number in `{}` ({})'.format(op, num))
                if convert:
                    setattr(self, _op, num_d*GS.kikit_units_to_kicad[m.group(2)])

    def add_angle(self, ops, def_units=None):
        if def_units is None:
            def_units = self._parent._parent.units
        for op in ops:
            val = getattr(self, op)
            if isinstance(val, (int, float)):
                setattr(self, op, str(val)+def_units)
            else:
                m = PanelOptions._ang_regex.match(val)
                if m is None:
                    raise KiPlotConfigurationError('Malformed angle `{}: {}` must be a number and its type'.format(op, val))
                num = m.group(1)
                try:
                    num_d = float(num)
                except ValueError:
                    num_d = None
                if num_d is None:
                    raise KiPlotConfigurationError('Malformed number in `{}` ({})'.format(op, num))
