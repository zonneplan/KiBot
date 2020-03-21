# -*- coding: utf-8 -*-

import argparse
import logging
import os
import sys

from . import kiplot
from . import config_reader
from . import log
from . import misc


def main():

    parser = argparse.ArgumentParser(
        description='Command-line Plotting for KiCad')
    parser.add_argument('target', nargs='*',
                        help='Outputs to generate, default is all')
    group = parser.add_mutually_exclusive_group()
    parser.add_argument('-b', '--board-file', required=True,
                        help='The PCB .kicad-pcb board file')
    parser.add_argument('-c', '--plot-config', required=True,
                        help='The plotting config file to use')
    parser.add_argument('-d', '--out-dir', default='.',
                        help='The output directory (cwd if not given)')
    parser.add_argument('-i', '--invert-sel', action='store_true',
                        help='Generate the outputs not listed as targets')
    group.add_argument('-q', '--quiet', action='store_true',
                        help='remove information logs')
    parser.add_argument('-s', '--skip-pre', nargs=1,
                        help='skip pre-flight actions, comma separated list or `all`')
    group.add_argument('-v', '--verbose', action='store_true',
                        help='show debugging information')

    args = parser.parse_args()

    # Create a logger with the specified verbosity
    logger = log.init(args.verbose, args.quiet)

    if not os.path.isfile(args.board_file):
        logger.error("Board file not found: {}".format(args.board_file))
        sys.exit(misc.NO_PCB_FILE)

    if not os.path.isfile(args.plot_config):
        logger.error("Plot config file not found: {}"
                      .format(args.plot_config))
        sys.exit(misc.EXIT_BAD_ARGS)

    cr = config_reader.CfgYamlReader(args.board_file)

    with open(args.plot_config) as cf_file:
        cfg = cr.read(cf_file)

    # relative to CWD (absolute path overrides)
    outdir = os.path.join(os.getcwd(), args.out_dir)
    cfg.outdir = outdir

    # Finally, once all value are in, check they make sense
    errs = cfg.validate()

    if errs:
        logger.error('Invalid config:\n\n' + "\n".join(errs))
        sys.exit(misc.EXIT_BAD_CONFIG)

    # Set up the plotter and do it
    plotter = kiplot.Plotter(cfg)
    plotter.plot(args.board_file, args.target, args.invert_sel, args.skip_pre)


if __name__ == "__main__":
    main()
