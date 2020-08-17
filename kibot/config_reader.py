# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
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
from .misc import (NO_YAML_MODULE, EXIT_BAD_ARGS, EXAMPLE_CFG, WONT_OVERWRITE)
from .gs import GS
from .reg_out import RegOutput
from .pre_base import BasePreFlight

# Logger
from . import log

logger = log.get_logger(__name__)

try:
    import yaml
except ImportError:  # pragma: no cover
    log.init(False, False)
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
            name = o_tree['name']
        except KeyError:
            config_error("Output needs a name in: "+str(o_tree))

        try:
            otype = o_tree['type']
        except KeyError:
            config_error("Output `"+name+"` needs a type")

        name_type = "`"+name+"` ("+otype+")"

        # Is a valid type?
        if not RegOutput.is_registered(otype):
            config_error("Unknown output type: `{}`".format(otype))
        # Load it
        logger.debug("Parsing output options for "+name_type)
        o_out = RegOutput.get_class_for(otype)()
        o_out.set_tree(o_tree)
        # Set the data we already know, so we can skip the configurations that aren't requested
        o_out.name = name
        o_out.type = otype

        return o_out

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
            config_error("Incorrect `global` section")

        for k, v in gb.items():
            if k == 'output':
                if not isinstance(v, str):
                    config_error("Global `output` must be a string")
                GS.global_output = v
            else:
                logger.warning("Unknown global option `{}`".format(k))

    def read(self, fstream):
        """
        Read a file object into a config object

        :param fstream: file stream of a config YAML file
        """
        try:
            data = yaml.safe_load(fstream)
        except yaml.YAMLError as e:
            config_error("Error loading YAML "+str(e))
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
            elif k == 'outputs':
                if isinstance(v, list):
                    for o in v:
                        outputs.append(self._parse_output(o))
                else:
                    config_error("`outputs` must be a list")
            else:
                config_error('Unknown section `{}` in config.'.format(k))
        if version is None:
            config_error("YAML config needs `kibot.version`.")
        return outputs


def trim(docstring):
    """ PEP 257 recommended trim for __doc__ """
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
            help = 'Undocumented'  # pragma: no cover
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
        lines = ['Undocumented', 'No description']  # pragma: no cover
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
            help = 'Undocumented'  # pragma: no cover
        print('- {}: {}.'.format(n, help.strip()))
        if options:
            print_output_options(n, options, 2)


def print_example_options(f, cls, name, indent, po):
    ind_str = indent*' '
    obj = cls()
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
            elif hasattr(val, '_default'):
                f.write(ind_str+'{}: {}\n'.format(k, val._default))
            else:
                f.write(ind_str+'{}:\n'.format(k))
                print_example_options(f, val, '', indent+2, None)
        else:
            f.write(ind_str+'{}: {}\n'.format(k, val))
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
        f.write('kibot:\n  version: 1\n')
        # Preflights
        f.write('\npreflight:\n')
        pres = BasePreFlight.get_registered()
        for n, o in OrderedDict(sorted(pres.items())).items():
            if o.__doc__:
                f.write('  #'+o.__doc__.rstrip()+'\n')
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
                lines = ['Undocumented', 'No description']  # pragma: no cover
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
