# -*- coding: utf-8 -*-
"""KiPlot: Command-line Plotting for KiCad

Usage:
  kiplot [-b BOARD] [-c CONFIG] [-d OUT_DIR] [-s PRE] [-q | -v...] [-i]
         [TARGET...]
  kiplot [-b BOARD] [-c PLOT_CONFIG] --list
  kiplot --help-list-outputs
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
  --help-list-outputs              List supported outputs
  --help-output HELP_OUTPUT        Help for this particular output
  --help-outputs                   List supported outputs and details
  --help-preflights                List supported preflights and details
  -i, --invert-sel                 Generate the outputs not listed as targets
  -l, --list                       List available outputs (in the config file)
  -q, --quiet                      Remove information logs
  -s PRE, --skip-pre PRE           Skip preflights, comma separated or `all`
  -v, --verbose                    Show debugging information
  --version, -V                    Show program's version number and exit

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
from glob import glob
from logging import DEBUG

# Import log first to set the domain
from . import log
log.set_domain('kiplot')
from .kiplot import (GS, generate_outputs)
from .pre_base import (BasePreFlight)
from .config_reader import (CfgYamlReader, print_outputs_help, print_output_help, print_preflights_help)
from .misc import (NO_PCB_FILE, EXIT_BAD_ARGS)
from .docopt import docopt
from .__version__ import __version__


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
            logger.info('- '+str(o))


def main():
    ver = 'KiPlot '+__version__+' - '+__copyright__+' - License: '+__license__
    args = docopt(__doc__, version=ver, options_first=True)

    # Create a logger with the specified verbosity
    logger = log.init(args.verbose, args.quiet)
    GS.debug_enabled = logger.getEffectiveLevel() <= DEBUG

    # Output dir: relative to CWD (absolute path overrides)
    GS.out_dir = os.path.join(os.getcwd(), args.out_dir)

    if args.help_outputs or args.help_list_outputs:
        print_outputs_help(details=args.help_outputs)
        sys.exit(0)
    if args.help_output:
        print_output_help(args.help_output)
        sys.exit(0)
    if args.help_preflights:
        print_preflights_help()
        sys.exit(0)

    # Determine the PCB file
    if args.board_file is None:
        board_files = glob('*.kicad_pcb')
        if len(board_files) == 1:
            board_file = board_files[0]
            logger.info('Using PCB file: '+board_file)
        elif len(board_files) > 1:
            board_file = board_files[0]
            logger.warning('More than one PCB file found in current directory.\n'
                           '  Using '+board_file+' if you want to use another use -b option.')
        else:
            logger.error('No PCB file found (*.kicad_pcb), use -b to specify one.')
            sys.exit(EXIT_BAD_ARGS)
    else:
        board_file = args.board_file
    if not os.path.isfile(board_file):
        logger.error("Board file not found: "+board_file)
        sys.exit(NO_PCB_FILE)
    GS.pcb_file = board_file
    GS.sch_file = os.path.splitext(board_file)[0] + '.sch'
    if not os.path.isfile(GS.sch_file):
        logger.warning('Missing schematic file: ' + GS.sch_file)
        GS.sch_file = None

    # Determine the YAML file
    if args.plot_config is None:
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
    else:
        plot_config = args.plot_config
    if not os.path.isfile(plot_config):
        logger.error("Plot config file not found: "+plot_config)
        sys.exit(EXIT_BAD_ARGS)

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

    generate_outputs(outputs, args.target, args.invert_sel, args.skip_pre)


if __name__ == "__main__":
    main()  # pragma: no cover
