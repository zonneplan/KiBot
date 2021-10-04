# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2018 John Beard
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot
"""
Class to read KiBot config files
"""

import os
from sys import (exit, maxsize)
from collections import OrderedDict

from .error import (KiPlotConfigurationError, config_error)
from .kiplot import (load_board)
from .misc import (NO_YAML_MODULE, EXIT_BAD_ARGS, EXAMPLE_CFG, WONT_OVERWRITE, W_NOOUTPUTS, W_UNKOUT, W_NOFILTERS,
                   W_NOVARIANTS)
from .gs import GS
from .registrable import RegOutput, RegVariant, RegFilter
from .pre_base import BasePreFlight

# Logger
from . import log

logger = log.get_logger(__name__)

try:
    import yaml
except ImportError:
    log.init()
    logger.error('No yaml module for Python, install python3-yaml')
    exit(NO_YAML_MODULE)


class CfgYamlReader(object):
    def __init__(self):
        super().__init__()

    def _check_version(self, v):
        if not isinstance(v, dict):
            config_error("Incorrect `kibot` section")
        if 'version' not in v:
            config_error("YAML config needs `kibot.version`.")
        version = v['version']
        # Only version 1 is known
        if version != 1:
            config_error("Unknown KiBot config version: "+str(version))
        return version

    def _parse_output(self, o_tree):
        try:
            name = str(o_tree['name'])
            if not name:
                raise KeyError
        except KeyError:
            config_error("Output needs a name in: "+str(o_tree))

        try:
            otype = o_tree['type']
            if not otype:
                raise KeyError
        except KeyError:
            config_error("Output `"+name+"` needs a type")

        try:
            comment = o_tree['comment']
        except KeyError:
            comment = ''
        if comment is None:
            comment = ''

        name_type = "`"+name+"` ("+otype+")"

        # Is a valid type?
        if not RegOutput.is_registered(otype):
            config_error("Unknown output type: `{}`".format(otype))
        # Load it
        logger.debug("Pre-parsing output options for "+name_type)
        o_out = RegOutput.get_class_for(otype)()
        o_out.set_tree(o_tree)
        # Set the data we already know, so we can skip the configurations that aren't requested
        o_out.name = name
        o_out.type = otype
        o_out.comment = comment

        return o_out

    def _parse_outputs(self, v):
        outputs = []
        if isinstance(v, list):
            for o in v:
                outputs.append(self._parse_output(o))
        else:
            config_error("`outputs` must be a list")
        return outputs

    def _parse_variant(self, o_tree, kind, reg_class):
        kind_f = kind[0].upper()+kind[1:]
        try:
            name = str(o_tree['name'])
            if not name:
                raise KeyError
        except KeyError:
            config_error(kind_f+" needs a name in: "+str(o_tree))
        try:
            otype = o_tree['type']
            if not otype:
                raise KeyError
        except KeyError:
            config_error(kind_f+" `"+name+"` needs a type")
        # Is a valid type?
        if not reg_class.is_registered(otype):
            config_error("Unknown {} type: `{}`".format(kind, otype))
        # Load it
        name_type = "`"+name+"` ("+otype+")"
        logger.debug("Parsing "+kind+" "+name_type)
        o_var = reg_class.get_class_for(otype)()
        o_var.set_tree(o_tree)
        try:
            o_var.config(None)
        except KiPlotConfigurationError as e:
            config_error("In section `"+name_type+"`: "+str(e))
        return o_var

    def _parse_variants(self, v):
        variants = {}
        if isinstance(v, list):
            for o in v:
                o_var = self._parse_variant(o, 'variant', RegVariant)
                variants[o_var.name] = o_var
        else:
            config_error("`variants` must be a list")
        return variants

    def _parse_filters(self, v):
        filters = {}
        if isinstance(v, list):
            for o in v:
                o_fil = self._parse_variant(o, 'filter', RegFilter)
                filters[o_fil.name] = o_fil
        else:
            config_error("`filters` must be a list")
        return filters

    def _parse_preflight(self, pf):
        logger.debug("Parsing preflight options: {}".format(pf))
        if not isinstance(pf, dict):
            config_error("Incorrect `preflight` section")

        for k, v in pf.items():
            if not BasePreFlight.is_registered(k):
                config_error("Unknown preflight: `{}`".format(k))
            try:
                logger.debug("Parsing preflight "+k)
                o_pre = BasePreFlight.get_class_for(k)(k, v)
            except KiPlotConfigurationError as e:
                config_error("In preflight '"+k+"': "+str(e))
            BasePreFlight.add_preflight(o_pre)

    def _parse_global(self, gb):
        """ Get global options """
        logger.debug("Parsing global options: {}".format(gb))
        if not isinstance(gb, dict):
            config_error("Incorrect `global` section (must be a dict)")
        # Parse all keys inside it
        glb = GS.global_opts_class()
        glb.set_tree(gb)
        try:
            glb.config(None)
        except KiPlotConfigurationError as e:
            config_error("In `global` section: "+str(e))

    @staticmethod
    def _config_error_import(fname, error):
        if fname is None:
            fname = '*unnamed*'
        config_error('{} in {} import'.format(error, fname))

    @staticmethod
    def _parse_import_items(kind, fname, value):
        if isinstance(value, str):
            if value == 'all':
                return None
            elif value == 'none':
                return []
            return [value]
        if isinstance(value, list):
            values = []
            for v in value:
                if isinstance(v, str):
                    values.append(v)
                else:
                    CfgYamlReader._config_error_import(fname, '`{}` items must be strings ({})'.format(kind, str(v)))
            return values
        CfgYamlReader._config_error_import(fname, '`{}` must be a string or a list ({})'.format(kind, str(v)))

    def _parse_import(self, imp, name):
        """ Get imports """
        logger.debug("Parsing imports: {}".format(imp))
        if not isinstance(imp, list):
            config_error("Incorrect `import` section (must be a list)")
        # Import the files
        dir = os.path.dirname(os.path.abspath(name))
        outputs = []
        for entry in imp:
            if isinstance(entry, str):
                fn = entry
                outs = None
                fils = []
                vars = []
                explicit_outs = True
                explicit_fils = False
                explicit_vars = False
            elif isinstance(entry, dict):
                fn = outs = fils = vars = None
                explicit_outs = explicit_fils = explicit_vars = False
                for k, v in entry.items():
                    if k == 'file':
                        if not isinstance(v, str):
                            config_error("`import.file` must be a string ({})".format(str(v)))
                        fn = v
                    elif k == 'outputs':
                        outs = self._parse_import_items('outputs', fn, v)
                        explicit_outs = True
                    elif k == 'filters':
                        fils = self._parse_import_items('filters', fn, v)
                        explicit_fils = True
                    elif k == 'variants':
                        vars = self._parse_import_items('variants', fn, v)
                        explicit_vars = True
                    else:
                        self._config_error_import(fname, "unknown import entry `{}`".format(str(v)))
                if fn is None:
                    config_error("`import` entry without `file` ({})".format(str(entry)))
            else:
                config_error("`import` items must be strings or dicts ({})".format(str(entry)))
            if not os.path.isabs(fn):
                fn = os.path.join(dir, fn)
            if not os.path.isfile(fn):
                config_error("missing import file `{}`".format(fn))
            fn_rel = os.path.relpath(fn)
            data = self.load_yaml(open(fn))
            # Outputs
            if (outs is None or len(outs) > 0) and 'outputs' in data:
                i_outs = self._parse_outputs(data['outputs'])
                if outs is not None:
                    sel_outs = []
                    for o in i_outs:
                        if o.name in outs:
                            sel_outs.append(o)
                            outs.remove(o)
                    for o in outs:
                        logger.warning(W_UNKOUT+"can't import `{}` output from `{}` (missing)".format(o, fn_rel))
                else:
                    sel_outs = i_outs
                if len(sel_outs) == 0:
                    logger.warning(W_NOOUTPUTS+"No outputs found in `{}`".format(fn_rel))
                else:
                    outputs.extend(sel_outs)
                logger.debug('Outputs loaded from `{}`: {}'.format(fn_rel, list(map(lambda c: c.name, sel_outs))))
            if outs is None and explicit_outs and 'outputs' not in data:
                logger.warning(W_NOOUTPUTS+"No outputs found in `{}`".format(fn_rel))
            # Filters
            if (fils is None or len(fils) > 0) and 'filters' in data:
                i_fils = self._parse_filters(data['filters'])
                if fils is not None:
                    sel_fils = {}
                    for f in fils:
                        if f in i_fils:
                            sel_fils[f] = i_fils[f]
                        else:
                            logger.warning(W_UNKOUT+"can't import `{}` filter from `{}` (missing)".format(f, fn_rel))
                else:
                    sel_fils = i_fils
                if len(sel_fils) == 0:
                    logger.warning(W_NOFILTERS+"No filters found in `{}`".format(fn_rel))
                else:
                    RegOutput.add_filters(sel_fils)
                    logger.debug('Filters loaded from `{}`: {}'.format(fn_rel, sel_fils.keys()))
            if fils is None and explicit_fils and 'filters' not in data:
                logger.warning(W_NOOUTPUTS+"No filters found in `{}`".format(fn_rel))
            # Variants
            if (vars is None or len(vars) > 0) and 'variants' in data:
                i_vars = self._parse_variants(data['variants'])
                if vars is not None:
                    sel_vars = {}
                    for f in vars:
                        if f in i_vars:
                            sel_vars[f] = i_vars[f]
                        else:
                            logger.warning(W_UNKOUT+"can't import `{}` variant from `{}` (missing)".format(f, fn_rel))
                else:
                    sel_vars = i_vars
                if len(sel_vars) == 0:
                    logger.warning(W_NOVARIANTS+"No variants found in `{}`".format(fn_rel))
                else:
                    RegOutput.add_variants(sel_vars)
                    logger.debug('Variants loaded from `{}`: {}'.format(fn_rel, sel_vars.keys()))
            if vars is None and explicit_vars and 'variants' not in data:
                logger.warning(W_NOOUTPUTS+"No variants found in `{}`".format(fn_rel))
        return outputs

    def load_yaml(self, fstream):
        try:
            data = yaml.safe_load(fstream)
        except yaml.YAMLError as e:
            config_error("Error loading YAML "+str(e))
        return data

    def read(self, fstream):
        """
        Read a file object into a config object

        :param fstream: file stream of a config YAML file
        """
        data = self.load_yaml(fstream)
        # Transfer command line global overwrites
        GS.global_output = GS.global_from_cli.get('output', None)
        GS.global_variant = GS.global_from_cli.get('variant', None)
        GS.global_kiauto_wait_start = GS.global_from_cli.get('kiauto_wait_start', None)
        GS.global_kiauto_time_out_scale = GS.global_from_cli.get('kiauto_time_out_scale', None)
        # List of outputs
        outputs = []
        version = None
        # Analize each section
        for k, v in data.items():
            # logger.debug('{} {}'.format(k, v))
            if k == 'kiplot' or k == 'kibot':
                version = self._check_version(v)
            elif k == 'preflight':
                self._parse_preflight(v)
            elif k == 'global':
                self._parse_global(v)
            elif k == 'import':
                outputs.extend(self._parse_import(v, fstream.name))
            elif k == 'variants':
                RegOutput.set_variants(self._parse_variants(v))
            elif k == 'filters':
                RegOutput.set_filters(self._parse_filters(v))
            elif k == 'outputs':
                outputs.extend(self._parse_outputs(v))
            else:
                config_error('Unknown section `{}` in config.'.format(k))
        if version is None:
            config_error("YAML config needs `kibot.version`.")
        return outputs


def trim(docstring):
    """ PEP 257 recommended trim for __doc__ """
    if docstring is None:
        return []
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    # while trimmed and not trimmed[-1]:
    #     trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return trimmed


def print_output_options(name, cl, indent):
    ind_str = indent*' '
    obj = cl()
    num_opts = 0
    for k, v in obj.get_attrs_gen():
        if k == 'type' and indent == 2:
            # Type is fixed for an output
            continue
        if not num_opts:
            # We found one, put the title
            print(ind_str+'* Valid keys:')
        help, alias, is_alias = obj.get_doc(k)
        if is_alias:
            help = 'Alias for '+alias
            entry = '  - *{}*: '
        else:
            entry = '  - `{}`: '
        if help is None:
            help = 'Undocumented'
        lines = help.split('\n')
        preface = ind_str+entry.format(k)
        clines = len(lines)
        print('{}{}{}'.format(preface, lines[0].strip(), '.' if clines == 1 else ''))
        ind_help = len(preface)*' '
        for ln in range(1, clines):
            text = lines[ln].strip()
            # Dots at the beggining are replaced by spaces.
            # Used to keep indentation.
            if text[0] == '.':
                for i in range(1, len(text)):
                    if text[i] != '.':
                        break
                text = ' '*i+text[i:]
            print('{}{}'.format(ind_help+text, '.' if ln+1 == clines else ''))
        num_opts = num_opts+1
        if isinstance(v, type):
            print_output_options('', v, indent+4)
    # if num_opts == 0:
    #     print(ind_str+'  - No available options')


def print_one_out_help(details, n, o):
    lines = trim(o.__doc__)
    if len(lines) == 0:
        lines = ['Undocumented', 'No description']
    if details:
        print('* '+lines[0])
        print('  * Type: `{}`'.format(n))
        print('  * Description: '+lines[1])
        for ln in range(2, len(lines)):
            print('                 '+lines[ln])
        print_output_options(n, o, 2)
    else:
        print('* {} [{}]'.format(lines[0], n))


def print_outputs_help(details=False):
    outs = RegOutput.get_registered()
    logger.debug('{} supported outputs'.format(len(outs)))
    print('Supported outputs:')
    for n, o in OrderedDict(sorted(outs.items())).items():
        if details:
            print()
        print_one_out_help(details, n, o)


def print_output_help(name):
    if not RegOutput.is_registered(name):
        logger.error('Unknown output type `{}`, try --help-list-outputs'.format(name))
        exit(EXIT_BAD_ARGS)
    print_one_out_help(True, name, RegOutput.get_class_for(name))


def print_preflights_help():
    pres = BasePreFlight.get_registered()
    logger.debug('{} supported preflights'.format(len(pres)))
    print('Supported preflight options:\n')
    for n, o in OrderedDict(sorted(pres.items())).items():
        help, options = o.get_doc()
        if help is None:
            help = 'Undocumented'
        print('- {}: {}.'.format(n, help.strip()))
        if options:
            print_output_options(n, options, 2)


def print_filters_help():
    fils = RegFilter.get_registered()
    logger.debug('{} supported filters'.format(len(fils)))
    print('Supported filters:\n')
    for n, o in OrderedDict(sorted(fils.items())).items():
        help = o.__doc__
        if help is None:
            help = 'Undocumented'
        print('- {}: {}.'.format(n, help.strip()))
        print_output_options(n, o, 2)


def print_example_options(f, cls, name, indent, po, is_list=False):
    ind_str = indent*' '
    obj = cls()
    first = True
    if po:
        obj.read_vals_from_po(po)
    for k, v in obj.get_attrs_gen():
        help, alias, is_alias = obj.get_doc(k)
        if is_alias:
            f.write(ind_str+'# `{}` is an alias for `{}`\n'.format(k, alias))
            continue
        if help:
            help_lines = help.split('\n')
            for hl in help_lines:
                # Dots at the beggining are replaced by spaces.
                # Used to keep indentation.
                hl = hl.strip()
                if hl[0] == '.':
                    for i in range(1, len(hl)):
                        if hl[i] != '.':
                            break
                    hl = ' '*i+hl[i:]
                f.write(ind_str+'# '+hl+'\n')
        example_attr = '_'+k+'_example'
        if hasattr(obj, example_attr):
            val = getattr(obj, example_attr)
        else:
            val = getattr(obj, k)
        if isinstance(val, str):
            val = "'{}'".format(val)
        elif isinstance(val, bool):
            val = str(val).lower()
        if isinstance(val, type):
            if val.__name__ == 'Optionable' and help and '=' in help_lines[0]:
                # Get the text after =
                txt = help_lines[0].split('=')[1]
                # Get the text before the space, without the ]
                txt = txt.split()[0][:-1]
                f.write(ind_str+'{}: {}\n'.format(k, txt))
            elif val.get_default():
                f.write(ind_str+'{}: {}\n'.format(k, val.get_default()))
            else:
                f.write(ind_str+'{}:\n'.format(k))
                print_example_options(f, val, '', indent+2, None, help and 'list(dict' in help_lines[0])
        else:
            if is_list and first:
                k = '- '+k
            f.write(ind_str+'{}: {}\n'.format(k, val))
            if is_list and first:
                ind_str += '  '
                first = False
    return obj


def create_example(pcb_file, out_dir, copy_options, copy_expand):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    fname = os.path.join(out_dir, EXAMPLE_CFG)
    if os.path.isfile(fname):
        logger.error(fname+" already exists, won't overwrite")
        exit(WONT_OVERWRITE)
    with open(fname, 'w') as f:
        logger.info('Creating {} example configuration'.format(fname))
        f.write("# ATTENTION! THIS ISN'T A FULLY FUNCTIONAL EXAMPLE.\n")
        f.write("# You should take portions of this example and edit the options to make\n")
        f.write("# them suitable for your use.\n")
        f.write("# This file is useful to know all the available options.\n")
        f.write('kibot:\n  version: 1\n')
        # Preflights
        f.write('\npreflight:\n')
        pres = BasePreFlight.get_registered()
        for n, o in OrderedDict(sorted(pres.items())).items():
            if o.__doc__:
                lines = trim(o.__doc__.rstrip()+'.')
                for ln in lines:
                    f.write('  # '+ln.rstrip()+'\n')
            f.write('  {}: {}\n'.format(n, o.get_example()))
        # Outputs
        outs = RegOutput.get_registered()
        f.write('\noutputs:\n')
        # List of layers
        po = None
        layers = 'all'
        if pcb_file:
            # We have a PCB to take as reference
            board = load_board(pcb_file)
            if copy_options or copy_expand:
                # Layers and plot options from the PCB
                layers = 'selected'
                po = board.GetPlotOptions()
        for n, cls in OrderedDict(sorted(outs.items())).items():
            lines = trim(cls.__doc__)
            if len(lines) == 0:
                lines = ['Undocumented', 'No description']
            f.write('  # '+lines[0].rstrip()+':\n')
            for ln in range(2, len(lines)):
                f.write('  # '+lines[ln].rstrip()+'\n')
            f.write("  - name: '{}_example'\n".format(n))
            f.write("    comment: '{}'\n".format(lines[1]))
            f.write("    type: '{}'\n".format(n))
            f.write("    dir: 'Example/{}_dir'\n".format(n))
            f.write("    options:\n")
            obj = cls()
            print_example_options(f, obj.options, n, 6, po)
            if 'layers' in obj.__dict__:
                if copy_expand:
                    f.write('    layers:\n')
                    layers = obj.layers.solve(layers)
                    for layer in layers:
                        f.write("      - layer: '{}'\n".format(layer.layer))
                        f.write("        suffix: '{}'\n".format(layer.suffix))
                        if layer.description:
                            f.write("        description: '{}'\n".format(layer.description))
                else:
                    f.write('    layers: {}\n'.format(layers))
            f.write('\n')
