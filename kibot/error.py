# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
KiBot errors
"""
from .gs import GS
from .misc import EXIT_BAD_CONFIG


class KiPlotError(Exception):
    pass


class PlotError(KiPlotError):
    pass


class KiPlotConfigurationError(KiPlotError):
    pass


def config_error(msg):
    GS.exit_with_error(msg, EXIT_BAD_CONFIG)
