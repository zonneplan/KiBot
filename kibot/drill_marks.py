# -*- coding: utf-8 -*-
# Copyright (c) 2020-2022 Salvador E. Tropea
# Copyright (c) 2020-2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from pcbnew import PCB_PLOT_PARAMS
from .error import KiPlotConfigurationError
from .out_any_layer import AnyLayerOptions
from . import log

logger = log.get_logger()

# Mappings to KiCad values
DRILL_MARKS_MAP = {
                   'none': PCB_PLOT_PARAMS.NO_DRILL_SHAPE,
                   'small': PCB_PLOT_PARAMS.SMALL_DRILL_SHAPE,
                   'full': PCB_PLOT_PARAMS.FULL_DRILL_SHAPE,
                  }
# Mappings from KiCad values
DRILL_MARKS_REV_MAP = {
                       PCB_PLOT_PARAMS.NO_DRILL_SHAPE: 'none',
                       PCB_PLOT_PARAMS.SMALL_DRILL_SHAPE: 'small',
                       PCB_PLOT_PARAMS.FULL_DRILL_SHAPE: 'full',
                      }
DRILL_MARKS_HELP = "[none,small,full] What to use to indicate the drill places, can be none, small or full (for real scale)"


def drill_marks_setter(val):
    if val not in DRILL_MARKS_MAP:
        raise KiPlotConfigurationError("Unknown drill mark type: {}".format(val))
    return val


def drill_marks_help(self):
    self._drill_marks = 'full'
    self.set_doc('drill_marks', " [string='full'] "+DRILL_MARKS_HELP)


class DrillMarks(AnyLayerOptions):
    """ This class provides the drill_marks attribute.
        Used by DXF, HPGL, PDF, PS and SVG formats. """
    def __init__(self):
        super().__init__()
        drill_marks_help(self)

    @property
    def drill_marks(self):
        return self._drill_marks

    @drill_marks.setter
    def drill_marks(self, val):
        self._drill_marks = drill_marks_setter(val)

    def config(self, parent):
        super().config(parent)
        self._drill_marks = DRILL_MARKS_MAP[self._drill_marks]

    def _configure_plot_ctrl(self, po, output_dir):
        super()._configure_plot_ctrl(po, output_dir)
        # How we draw drill marks
        po.SetDrillMarksType(self._drill_marks)

    def read_vals_from_po(self, po):
        super().read_vals_from_po(po)
        self._drill_marks = DRILL_MARKS_REV_MAP[po.GetDrillMarksType()]
