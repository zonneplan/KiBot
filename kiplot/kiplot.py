"""
Main Kiplot code
"""

import os
import re
from sys import exit
from shutil import which
from subprocess import (run, PIPE)
from distutils.version import StrictVersion

from .gs import (GS)
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


class Layer(object):
    """ A layer description """
    # Default names
    DEFAULT_LAYER_NAMES = {
        'F.Cu': pcbnew.F_Cu,
        'B.Cu': pcbnew.B_Cu,
        'F.Adhes': pcbnew.F_Adhes,
        'B.Adhes': pcbnew.B_Adhes,
        'F.Paste': pcbnew.F_Paste,
        'B.Paste': pcbnew.B_Paste,
        'F.SilkS': pcbnew.F_SilkS,
        'B.SilkS': pcbnew.B_SilkS,
        'F.Mask': pcbnew.F_Mask,
        'B.Mask': pcbnew.B_Mask,
        'Dwgs.User': pcbnew.Dwgs_User,
        'Cmts.User': pcbnew.Cmts_User,
        'Eco1.User': pcbnew.Eco1_User,
        'Eco2.User': pcbnew.Eco2_User,
        'Edge.Cuts': pcbnew.Edge_Cuts,
        'Margin': pcbnew.Margin,
        'F.CrtYd': pcbnew.F_CrtYd,
        'B.CrtYd': pcbnew.B_CrtYd,
        'F.Fab': pcbnew.F_Fab,
        'B.Fab': pcbnew.B_Fab,
    }
    # Default names
    DEFAULT_LAYER_DESC = {
        'F.Cu': 'Front copper',
        'B.Cu': 'Bottom copper',
        'F.Adhes': 'Front adhesive (glue)',
        'B.Adhes': 'Bottom adhesive (glue)',
        'F.Paste': 'Front solder paste',
        'B.Paste': 'Bottom solder paste',
        'F.SilkS': 'Front silkscreen (artwork)',
        'B.SilkS': 'Bottom silkscreen (artwork)',
        'F.Mask': 'Front soldermask (negative)',
        'B.Mask': 'Bottom soldermask (negative)',
        'Dwgs.User': 'User drawings',
        'Cmts.User': 'User comments',
        'Eco1.User': 'For user usage 1',
        'Eco2.User': 'For user usage 2',
        'Edge.Cuts': 'Board shape',
        'Margin': 'Margin relative to edge cut',
        'F.CrtYd': 'Front courtyard area',
        'B.CrtYd': 'Bottom courtyard area',
        'F.Fab': 'Front documentation',
        'B.Fab': 'Bottom documentation',
    }
    # Names from the board file
    pcb_layers = {}
    plot_layers = {}

    def __init__(self, name, suffix, desc):
        self.id = pcbnew.UNDEFINED_LAYER
        self.is_inner = False
        self.name = name
        self.suffix = suffix
        if desc is None and name in Layer.DEFAULT_LAYER_DESC:
            desc = Layer.DEFAULT_LAYER_DESC[name]
        self.desc = desc

    @staticmethod
    def set_pcb_layers(board):
        for id in board.GetEnabledLayers().Seq():
            Layer.pcb_layers[board.GetLayerName(id)] = id

    @staticmethod
    def _get_layers(d_layers):
        layers = []
        for n, id in d_layers.items():
            s = n.replace('.', '_')
            d = Layer.DEFAULT_LAYER_DESC.get(n)
            layers.append(Layer(n, s, d))
        return layers

    @staticmethod
    def get_pcb_layers():
        return Layer._get_layers(Layer.pcb_layers)

    @staticmethod
    def set_plot_layers(board):
        enabled = board.GetEnabledLayers().Seq()
        for id in board.GetPlotOptions().GetLayerSelection().Seq():
            if id in enabled:
                Layer.plot_layers[board.GetLayerName(id)] = id

    @staticmethod
    def get_plot_layers():
        return Layer._get_layers(Layer.plot_layers)

    def get_layer_id_from_name(self, layer_cnt):
        """ Get the pcbnew layer from the string provided in the config """
        # Priority
        # 1) Internal list
        if self.name in Layer.DEFAULT_LAYER_NAMES:
            self.id = Layer.DEFAULT_LAYER_NAMES[self.name]
        else:
            id = Layer.pcb_layers.get(self.name)
            if id is not None:
                # 2) List from the PCB
                self.id = id
                self.is_inner = id < pcbnew.B_Cu
            elif self.name.startswith("Inner"):
                # 3) Inner.N names
                m = re.match(r"^Inner\.([0-9]+)$", self.name)
                if not m:
                    raise PlotError("Malformed inner layer name: {}, use Inner.N".format(self.name))
                self.id = int(m.group(1))
                self.is_inner = True
            else:
                raise PlotError("Unknown layer name: "+self.name)
            # Check if the layer is in use
            if self.is_inner and (self.id < 1 or self.id >= layer_cnt - 1):
                raise PlotError("Inner layer `{}` is not valid for this board".format(self))
        return self.id

    @staticmethod
    def get_default_layers():
        layers = []
        for n, d in Layer.DEFAULT_LAYER_DESC.items():
            s = n.replace('.', '_')
            layers.append(Layer(n, s, d))
        return layers

    def __str__(self):
        return "{} ({} '{}' {})".format(self.name, self.id, self.desc, self.suffix)


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


def load_board(pcb_file=None):
    if not pcb_file:
        GS.check_pcb()
        pcb_file = GS.pcb_file
    try:
        board = pcbnew.LoadBoard(pcb_file)
        if BasePreFlight.get_option('check_zone_fills'):
            pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        # Now we know the names of the layers for this board
        Layer.set_pcb_layers(board)
        Layer.set_plot_layers(board)
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
            if out.is_sch():
                GS.check_sch()
            try:
                out.run(get_output_dir(out.get_outdir()), board)
            except PlotError as e:
                logger.error("In output `"+str(out)+"`: "+str(e))
                exit(PLOT_ERROR)
        else:
            logger.debug('Skipping `%s` output', str(out))
