from pcbnew import (PCB_PLOT_PARAMS)
from .error import KiPlotConfigurationError
from kiplot.macros import macros, document, output_class  # noqa: F401


class DrillMarks(object):
    """ This class provides the drill_marks attribute.
        Used by DXF, HPGL, PDF, PS and SVG formats. """
    # Mappings to KiCad values
    _drill_marks_map = {
                        'none': PCB_PLOT_PARAMS.NO_DRILL_SHAPE,
                        'small': PCB_PLOT_PARAMS.SMALL_DRILL_SHAPE,
                        'full': PCB_PLOT_PARAMS.FULL_DRILL_SHAPE,
                       }

    def __init__(self):
        with document:
            self._drill_marks = 'full'
            """ what to use to indicate the drill places, can be none, small or full (for real scale) """  # pragma: no cover

    @property
    def drill_marks(self):
        return self._drill_marks

    @drill_marks.setter
    def drill_marks(self, val):
        if val not in self._drill_marks_map:
            raise KiPlotConfigurationError("Unknown drill mark type: {}".format(val))
        self._drill_marks = val

    def config(self):
        self._drill_marks = DrillMarks._drill_marks_map[self._drill_marks]
