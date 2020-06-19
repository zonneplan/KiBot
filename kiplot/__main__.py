# -*- coding: utf-8 -*-
__author__ = 'John Beard, Salvador E. Tropea'
__copyright__ = 'Copyright 2018-2020, INTI/John Beard/Salvador E. Tropea'
__credits__ = ['Salvador E. Tropea', 'John Beard']
__license__ = 'GPL v3+'
__email__ = 'salvador@inti.gob.ar'
__status__ = 'beta'

import argparse
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
from .config_reader import (CfgYamlReader)
from .misc import (NO_PCB_FILE, EXIT_BAD_ARGS)
from .__version__ import __version__


def main():
    parser = argparse.ArgumentParser(description='Command-line Plotting for KiCad')
    parser.add_argument('target', nargs='*', help='Outputs to generate, default is all')
    group = parser.add_mutually_exclusive_group()
    parser.add_argument('-b', '--board-file', help='The PCB .kicad-pcb board file')
    parser.add_argument('-c', '--plot-config', help='The plotting config file to use')
    parser.add_argument('-d', '--out-dir', default='.', help='The output directory (cwd if not given)')
    parser.add_argument('-i', '--invert-sel', action='store_true', help='Generate the outputs not listed as targets')
    parser.add_argument('-l', '--list', action='store_true', help='List available outputs')
    group.add_argument('-q', '--quiet', action='store_true', help='remove information logs')
    parser.add_argument('-s', '--skip-pre', nargs=1, help='skip pre-flight actions, comma separated list or `all`')
    group.add_argument('-v', '--verbose', action='store_true', help='show debugging information')
    parser.add_argument('--version', '-V', action='version', version='%(prog)s '+__version__+' - ' +
                        __copyright__+' - License: '+__license__)
    args = parser.parse_args()

    # Create a logger with the specified verbosity
    logger = log.init(args.verbose, args.quiet)
    GS.debug_enabled = logger.getEffectiveLevel() <= DEBUG

    # Output dir: relative to CWD (absolute path overrides)
    GS.out_dir = os.path.join(os.getcwd(), args.out_dir)

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
    cr = CfgYamlReader(board_file)
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

    # Actions
    if args.list:
        logger.info('\nPre-flight:')
        pf = BasePreFlight.get_in_use_objs()
        for c in pf:
            logger.info('- '+str(c))
        logger.info('Outputs:')
        for o in outputs:
            logger.info('- '+str(o))
    else:
        generate_outputs(outputs, args.target, args.invert_sel, args.skip_pre)


if __name__ == "__main__":
    main()  # pragma: no cover
