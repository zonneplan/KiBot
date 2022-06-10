# -*- coding: utf-8 -*-
# Copyright (c) 2020-2022 Salvador E. Tropea
# Copyright (c) 2020-2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from pcbnew import PCB_PLOT_PARAMS
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


def add_drill_marks(self):
    self.drill_marks = 'full'
    self.set_doc('drill_marks', " [string='full'] [none,small,full] What to use to indicate the drill places, can be "
                 "none, small or full (for real scale)")


class DrillMarks(AnyLayerOptions):
    """ This class provides the drill_marks attribute.
        Used by DXF, HPGL, PDF, PS and SVG formats. """
    def __init__(self):
        super().__init__()
        add_drill_marks(self)

    def config(self, parent):
        super().config(parent)
        self.drill_marks = DRILL_MARKS_MAP[self.drill_marks]

    def _configure_plot_ctrl(self, po, output_dir):
        super()._configure_plot_ctrl(po, output_dir)
        # How we draw drill marks
        po.SetDrillMarksType(self.drill_marks)

    def read_vals_from_po(self, po):
        super().read_vals_from_po(po)
        self.drill_marks = DRILL_MARKS_REV_MAP[po.GetDrillMarksType()]
