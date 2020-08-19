# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2018 John Beard
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot
"""
Main KiBot code
"""

import os
import re
from sys import exit
from shutil import which
from subprocess import run, PIPE, call
from glob import glob
from distutils.version import StrictVersion
from importlib.util import (spec_from_file_location, module_from_spec)

from .gs import (GS)
from .misc import (PLOT_ERROR, NO_PCBNEW_MODULE, MISSING_TOOL, CMD_EESCHEMA_DO, URL_EESCHEMA_DO, CORRUPTED_PCB,
                   EXIT_BAD_ARGS, CORRUPTED_SCH, EXIT_BAD_CONFIG, WRONG_INSTALL)
from .error import PlotError, KiPlotConfigurationError, config_error, trace_dump
from .pre_base import BasePreFlight
from .kicad.v5_sch import Schematic, SchFileError
from .kicad.config import KiConfError
from . import log

logger = log.get_logger(__name__)
# Cache to avoid running external many times to check their versions
script_versions = {}


try:
    import pcbnew
except ImportError:  # pragma: no cover
    log.init(False, False)
    logger.error("Failed to import pcbnew Python module."
                 " Is KiCad installed?"
                 " Do you need to add it to PYTHONPATH?")
    exit(NO_PCBNEW_MODULE)


def _import(name, path):
    # Python 3.4+ import mechanism
    spec = spec_from_file_location("kibot."+name, path)
    mod = module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except ImportError:
        trace_dump()
        logger.error('Unable to import plug-ins')
        exit(WRONG_INSTALL)


def _load_actions(path):
    logger.debug("Importing from "+path)
    lst = glob(os.path.join(path, 'out_*.py')) + glob(os.path.join(path, 'pre_*.py'))
    for p in lst:
        name = os.path.splitext(os.path.basename(p))[0]
        logger.debug("- Importing "+name)
        _import(name, p)


def load_actions():
    """ Load all the available ouputs and preflights """
    from kibot.mcpy import activate
    # activate.activate()
    _load_actions(os.path.abspath(os.path.dirname(__file__)))
    home = os.environ.get('HOME')
    if home:
        dir = os.path.join(home, '.config', 'kiplot', 'plugins')
        if os.path.isdir(dir):
            _load_actions(dir)
        dir = os.path.join(home, '.config', 'kibot', 'plugins')
        if os.path.isdir(dir):
            _load_actions(dir)
    if 'de_activate' in activate.__dict__:
        logger.debug('Deactivating macros')
        activate.de_activate()


def check_version(command, version):
    global script_versions
    if command in script_versions:
        return
    cmd = [command, '--version']
    logger.debug('Running: '+str(cmd))
    result = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    z = re.match(command + r' (\d+\.\d+\.\d+)', result.stdout)
    if not z:
        z = re.search(r'Version: (\d+\.\d+\.\d+)', result.stdout)
    if not z:
        logger.error('Unable to determine ' + command + ' version:\n' +
                     result.stdout)
        exit(MISSING_TOOL)
    res = z.groups()
    if StrictVersion(res[0]) < StrictVersion(version):
        logger.error('Wrong version for `'+command+'` ('+res[0]+'), must be ' +
                     version+' or newer.')
        exit(MISSING_TOOL)
    script_versions[command] = res[0]


def check_script(cmd, url, version=None):
    if which(cmd) is None:
        logger.error('No `'+cmd+'` command found.\n'
                     'Please install it, visit: '+url)
        exit(MISSING_TOOL)
    if version is not None:
        check_version(cmd, version)


def check_eeschema_do():
    check_script(CMD_EESCHEMA_DO, URL_EESCHEMA_DO, '1.4.0')


def exec_with_retry(cmd):
    logger.debug('Executing: '+str(cmd))
    retry = 2
    while retry:
        ret = call(cmd)
        retry -= 1
        if ret > 0 and ret < 128 and retry:
            logger.debug('Failed with error {}, retrying ...'.format(ret))
        else:
            return ret


def load_board(pcb_file=None):
    if not pcb_file:
        GS.check_pcb()
        pcb_file = GS.pcb_file
    try:
        board = pcbnew.LoadBoard(pcb_file)
        if BasePreFlight.get_option('check_zone_fills'):
            pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        GS.board = board
    except OSError as e:
        logger.error('Error loading PCB file. Corrupted?')
        logger.error(e)
        exit(CORRUPTED_PCB)
    assert board is not None
    logger.debug("Board loaded")
    return board


def load_sch():
    GS.kicad_version = pcbnew.GetBuildVersion()
    logger.debug('KiCad: '+GS.kicad_version)
    GS.check_sch()
    GS.sch = Schematic()
    try:
        GS.sch.load(GS.sch_file)
        GS.sch.load_libs(GS.sch_file)
        if GS.debug_level > 1:
            logger.debug('Schematic dependencies: '+str(GS.sch.get_files()))
    except SchFileError as e:
        trace_dump()
        logger.error('At line {} of `{}`: {}'.format(e.line, e.file, e.msg))
        logger.error('Line content: `{}`'.format(e.code))
        exit(CORRUPTED_SCH)
    except KiConfError as e:
        trace_dump()
        logger.error('At line {} of `{}`: {}'.format(e.line, e.file, e.msg))
        logger.error('Line content: `{}`'.format(e.code))
        exit(EXIT_BAD_CONFIG)


def preflight_checks(skip_pre):
    logger.debug("Preflight checks")

    if skip_pre is not None:
        if skip_pre == 'all':
            logger.debug("Skipping all pre-flight actions")
            return
        else:
            skip_list = skip_pre.split(',')
            for skip in skip_list:
                if skip == 'all':
                    logger.error('All can\'t be part of a list of actions '
                                 'to skip. Use `--skip all`')
                    exit(EXIT_BAD_ARGS)
                else:
                    if not BasePreFlight.is_registered(skip):
                        logger.error('Unknown preflight `{}`'.format(skip))
                        exit(EXIT_BAD_ARGS)
                    o_pre = BasePreFlight.get_preflight(skip)
                    if not o_pre:
                        logger.warning('`{}` preflight is not in use, no need to skip'.format(skip))
                    else:
                        logger.debug('Skipping `{}`'.format(skip))
                        o_pre.disable()
    BasePreFlight.run_enabled()


def get_output_dir(o_dir):
    # outdir is a combination of the config and output
    outdir = os.path.abspath(os.path.join(GS.out_dir, o_dir))
    # Create directory if needed
    logger.debug("Output destination: {}".format(outdir))
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    return outdir


def config_output(out):
    try:
        out.config()
    except KiPlotConfigurationError as e:
        config_error("In section '"+out.name+"' ("+out.type+"): "+str(e))


def generate_outputs(outputs, target, invert, skip_pre):
    logger.debug("Starting outputs for board {}".format(GS.pcb_file))
    preflight_checks(skip_pre)
    # Check if all must be skipped
    n = len(target)
    if n == 0 and invert:
        # Skip all targets
        logger.debug('Skipping all outputs')
        return
    # Generate outputs
    board = None
    for out in outputs:
        if (n == 0) or ((out.name in target) ^ invert):
            # Should we load the PCB?
            if out.is_pcb() and (board is None):
                board = load_board()
            if out.is_sch():
                load_sch()
            config_output(out)
            logger.info('- '+str(out))
            try:
                out.run(get_output_dir(out.dir), board)
            except PlotError as e:
                logger.error("In output `"+str(out)+"`: "+str(e))
                exit(PLOT_ERROR)
            except KiPlotConfigurationError as e:
                config_error("In section '"+out.name+"' ("+out.type+"): "+str(e))
        else:
            logger.debug('Skipping `%s` output', str(out))
