"""
Main Kiplot code
"""

import os
import re
from sys import exit
from shutil import which
from subprocess import (run, PIPE)
from distutils.version import StrictVersion

from .misc import (PLOT_ERROR, NO_PCBNEW_MODULE, MISSING_TOOL, CMD_EESCHEMA_DO, URL_EESCHEMA_DO, NO_SCH_FILE, CORRUPTED_PCB,
                   EXIT_BAD_ARGS)
from .error import (PlotError)
from .pre_base import BasePreFlight
from . import log

logger = log.get_logger(__name__)

try:
    import pcbnew
except ImportError:  # pragma: no cover
    log.init(False, False)
    logger.error("Failed to import pcbnew Python module."
                 " Is KiCad installed?"
                 " Do you need to add it to PYTHONPATH?")
    exit(NO_PCBNEW_MODULE)


class GS(object):
    """
    Class to keep the global settings.
    Is a static class, just a placeholder for some global variables.
    """
    pcb_file = None
    out_dir = None
    filter_file = None
    debug_enabled = False
    pcb_layers = None


class Layer(object):
    """ A layer description """
    def __init__(self, id, is_inner, name):
        self.id = id
        self.is_inner = is_inner
        self.name = name
        self.suffix = None
        self.desc = None

    def set_extra(self, suffix, desc):
        self.suffix = suffix
        self.desc = desc

    def __str__(self):
        return "{} ({} '{}' {})".format(self.name, self.id, self.desc, self.suffix)


def load_pcb_layers():
    """ Load layer names from the PCB """
    GS.pcb_layers = {}
    with open(GS.pcb_file, "r") as pcb_file:
        collect_layers = False
        for line in pcb_file:
            if collect_layers:
                z = re.match(r'\s+\((\d+)\s+(\S+)', line)
                if z:
                    res = z.groups()
                    # print(res[1]+'->'+res[0])
                    GS.pcb_layers[res[1]] = int(res[0])
                else:
                    if re.search(r'^\s+\)$', line):
                        collect_layers = False
                        break
            else:
                if re.search(r'\s+\(layers', line):
                    collect_layers = True


def get_layer_id_from_pcb(name):
    if GS.pcb_layers is None:
        load_pcb_layers()
    return GS.pcb_layers.get(name)


def check_version(command, version):
    cmd = [command, '--version']
    logger.debug('Running: '+str(cmd))
    result = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    z = re.match(command + r' (\d+\.\d+\.\d+)', result.stdout)
    if not z:
        logger.error('Unable to determine ' + command + ' version:\n' +
                     result.stdout)
        exit(MISSING_TOOL)
    res = z.groups()
    if StrictVersion(res[0]) < StrictVersion(version):
        logger.error('Wrong version for `'+command+'` ('+res[0]+'), must be ' +
                     version+' or newer.')
        exit(MISSING_TOOL)


def check_script(cmd, url, version=None):
    if which(cmd) is None:
        logger.error('No `'+cmd+'` command found.\n'
                     'Please install it, visit: '+url)
        exit(MISSING_TOOL)
    if version is not None:
        check_version(cmd, version)


def check_eeschema_do():
    check_script(CMD_EESCHEMA_DO, URL_EESCHEMA_DO, '1.4.0')
    if not GS.sch_file:
        logger.error('Missing schematic file')
        exit(NO_SCH_FILE)


def load_board():
    try:
        board = pcbnew.LoadBoard(GS.pcb_file)
        if BasePreFlight.get_option('check_zone_fills'):
            pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    except OSError as e:
        logger.error('Error loading PCB file. Currupted?')
        logger.error(e)
        exit(CORRUPTED_PCB)
    assert board is not None
    logger.debug("Board loaded")
    return board


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
    outdir = os.path.join(GS.out_dir, o_dir)
    # Create directory if needed
    logger.debug("Output destination: {}".format(outdir))
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    return outdir


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
        if (n == 0) or ((out.get_name() in target) ^ invert):
            logger.info('- '+str(out))
            # Should we load the PCB?
            if out.is_pcb() and (board is None):
                board = load_board()
            try:
                out.run(get_output_dir(out.get_outdir()), board)
            except PlotError as e:
                logger.error("In output `"+str(out)+"`: "+str(e))
                exit(PLOT_ERROR)
        else:
            logger.debug('Skipping `%s` output', str(out))
