"""
KiPlot errors
"""
from sys import (exit, exc_info)
from traceback import print_tb
from .gs import GS
from .misc import (EXIT_BAD_CONFIG)
# Logger
from . import log

logger = log.get_logger(__name__)


class KiPlotError(Exception):
    pass


class PlotError(KiPlotError):
    pass


class KiPlotConfigurationError(KiPlotError):
    pass


def config_error(msg):
    if GS.debug_enabled:
        logger.error('Trace stack:')
        (type, value, traceback) = exc_info()
        print_tb(traceback)
    logger.error(msg)
    exit(EXIT_BAD_CONFIG)
