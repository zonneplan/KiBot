# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2018 John Beard
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot
"""KiPlot: Command-line Plotting for KiCad

Usage:
  kiplot [-b BOARD] [-e SCHEMA] [-c CONFIG] [-d OUT_DIR] [-s PRE]
         [-q | -v...] [-i] [TARGET...]
  kiplot [-c PLOT_CONFIG] --list
  kiplot [-b BOARD] [-d OUT_DIR] [-p | -P] --example
  kiplot [-v...] --help-list-outputs
  kiplot --help-output=HELP_OUTPUT
  kiplot --help-outputs
  kiplot --help-preflights
  kiplot -h | --help
  kiplot --version

Arguments:
  TARGET    Outputs to generate, default is all

Options:
  -h, --help                       Show this help message and exit
  -b BOARD, --board-file BOARD     The PCB .kicad-pcb board file
  -c CONFIG, --plot-config CONFIG  The plotting config file to use
  -d OUT_DIR, --out-dir OUT_DIR    The output directory [default: .]
  -e SCHEMA, --schematic SCHEMA    The schematic file (.sch)
  --help-list-outputs              List supported outputs
  --help-output HELP_OUTPUT        Help for this particular output
  --help-outputs                   List supported outputs and details
  --help-preflights                List supported preflights and details
  -i, --invert-sel                 Generate the outputs not listed as targets
  -l, --list                       List available outputs (in the config file)
  -p, --copy-options               Copy plot options from the PCB file
  -P, --copy-and-expand            As -p but expand the list of layers
  -q, --quiet                      Remove information logs
  -s PRE, --skip-pre PRE           Skip preflights, comma separated or `all`
  -v, --verbose                    Show debugging information
  -V, --version                    Show program's version number and exit
  -x, --example                    Create an example configuration file.

"""
__author__ = 'John Beard, Salvador E. Tropea'
__copyright__ = 'Copyright 2018-2020, INTI/John Beard/Salvador E. Tropea'
__credits__ = ['Salvador E. Tropea', 'John Beard']
__license__ = 'GPL v3+'
__email__ = 'salvador@inti.gob.ar'
__status__ = 'beta'

import os
import sys
import gzip
import locale
from glob import glob
from logging import DEBUG

# Import log first to set the domain
from . import log
log.set_domain('kiplot')
from .gs import (GS)
from .kiplot import (generate_outputs, load_actions, config_output)
from .pre_base import (BasePreFlight)
from .config_reader import (CfgYamlReader, print_outputs_help, print_output_help, print_preflights_help, create_example)
from .misc import (NO_PCB_FILE, NO_SCH_FILE, EXIT_BAD_ARGS)
from .docopt import docopt
from .__version__ import __version__

logger = None


def list_pre_and_outs(logger, outputs):
    logger.info('Available actions:\n')
    pf = BasePreFlight.get_in_use_objs()
    if len(pf):
        logger.info('Pre-flight:')
        for c in pf:
            logger.info('- '+str(c))
    if len(outputs):
        logger.info('Outputs:')
        for o in outputs:
            config_output(o)
            logger.info('- '+str(o))


def solve_schematic(a_schematic, a_board_file):
    schematic = a_schematic
    if not schematic and a_board_file:
        sch = os.path.splitext(a_board_file)[0]+'.sch'
        if os.path.isfile(sch):
            schematic = sch
    if not schematic:
        schematics = glob('*.sch')
        if len(schematics) == 1:
            schematic = schematics[0]
            logger.info('Using SCH file: '+schematic)
        elif len(schematics) > 1:
            # Look for a schematic with a PCB
            boards = glob('*.kicad_pcb')
            boards_schs = [x[:-9]+'sch' for x in boards]
            for sch in schematics:
                if sch in boards_schs:
                    schematic = sch
                    break
            if schematic is None:
                schematic = schematics[0]
            logger.warning('More than one SCH file found in current directory.\n'
                           '  Using '+schematic+' if you want to use another use -e option.')
    if schematic and not os.path.isfile(schematic):
        logger.error("Schematic file not found: "+schematic)
        sys.exit(NO_SCH_FILE)
    if schematic:
        schematic = os.path.abspath(schematic)
        logger.debug('Using schematic: `{}`'.format(schematic))
    else:
        logger.debug('No schematic file found')
    return schematic


def solve_config(a_plot_config):
    plot_config = a_plot_config
    if not plot_config:
        plot_configs = glob('*.kiplot.yaml')
        if len(plot_configs) == 1:
            plot_config = plot_configs[0]
            logger.info('Using config file: '+plot_config)
        elif len(plot_configs) > 1:
            plot_config = plot_configs[0]
            logger.warning('More than one config file found in current directory.\n'
                           '  Using '+plot_config+' if you want to use another use -c option.')
        else:
            logger.error('No config file found (*.kiplot.yaml), use -c to specify one.')
            sys.exit(EXIT_BAD_ARGS)
    if not os.path.isfile(plot_config):
        logger.error("Plot config file not found: "+plot_config)
        sys.exit(EXIT_BAD_ARGS)
    logger.debug('Using configuration file: `{}`'.format(plot_config))
    return plot_config


def check_board_file(board_file):
    if board_file and not os.path.isfile(board_file):
        logger.error("Board file not found: "+board_file)
        sys.exit(NO_PCB_FILE)


def solve_board_file(schematic, a_board_file):
    board_file = a_board_file
    if not board_file and schematic:
        pcb = os.path.splitext(schematic)[0]+'.kicad_pcb'
        if os.path.isfile(pcb):
            board_file = pcb
    if not board_file:
        board_files = glob('*.kicad_pcb')
        if len(board_files) == 1:
            board_file = board_files[0]
            logger.info('Using PCB file: '+board_file)
        elif len(board_files) > 1:
            board_file = board_files[0]
            logger.warning('More than one PCB file found in current directory.\n'
                           '  Using '+board_file+' if you want to use another use -b option.')
    check_board_file(board_file)
    if board_file:
        logger.debug('Using PCB: `{}`'.format(board_file))
    else:
        logger.debug('No PCB file found')
    return board_file


def set_locale():
    """ Try to set the locale for all the cataegories.
        If it fails try with LC_NUMERIC (the one we need for tests). """
    try:
        locale.setlocale(locale.LC_ALL, '')
        return
    except locale.Error:
        pass
    try:
        locale.setlocale(locale.LC_NUMERIC, '')
        return
    except locale.Error:
        pass


def main():
    set_locale()
    ver = 'KiPlot '+__version__+' - '+__copyright__+' - License: '+__license__
    args = docopt(__doc__, version=ver, options_first=True)

    # Create a logger with the specified verbosity
    global logger
    logger = log.init(args.verbose, args.quiet)
    GS.debug_enabled = logger.getEffectiveLevel() <= DEBUG
    GS.debug_level = args.verbose

    # Output dir: relative to CWD (absolute path overrides)
    GS.out_dir = os.path.join(os.getcwd(), args.out_dir)

    # Load output and preflight plugins
    load_actions()

    if args.help_outputs or args.help_list_outputs:
        print_outputs_help(details=args.help_outputs)
        sys.exit(0)
    if args.help_output:
        print_output_help(args.help_output)
        sys.exit(0)
    if args.help_preflights:
        print_preflights_help()
        sys.exit(0)
    if args.example:
        check_board_file(args.board_file)
        if args.copy_options and not args.board_file:
            logger.error('Asked to copy options but no PCB specified.')
            sys.exit(EXIT_BAD_ARGS)
        create_example(args.board_file, GS.out_dir, args.copy_options, args.copy_and_expand)
        sys.exit(0)

    # Determine the YAML file
    plot_config = solve_config(args.plot_config)
    # Read the config file
    cr = CfgYamlReader()
    outputs = None
    try:
        # The Python way ...
        with gzip.open(plot_config) as cf_file:
            outputs = cr.read(cf_file)
    except OSError:
        pass
    if outputs is None:
        with open(plot_config) as cf_file:
            outputs = cr.read(cf_file)

    # Is just list the available targets?
    if args.list:
        list_pre_and_outs(logger, outputs)
        sys.exit(0)

    # Determine the SCH file
    GS.set_sch(solve_schematic(args.schematic, args.board_file))
    # Determine the PCB file
    GS.set_pcb(solve_board_file(GS.sch_file, args.board_file))

    generate_outputs(outputs, args.target, args.invert_sel, args.skip_pre)


if __name__ == "__main__":
    main()  # pragma: no cover
