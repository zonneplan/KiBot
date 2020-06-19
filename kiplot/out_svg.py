from pcbnew import PLOT_FORMAT_SVG
from .out_base import BaseOutput
from .out_any_layer import AnyLayer
from .error import KiPlotConfigurationError


class SVG(AnyLayer):
    def __init__(self, name, type, description):
        super(SVG, self).__init__(name, type, description)
        self._plot_format = PLOT_FORMAT_SVG
        # Options
        self.line_width = 0.25
        self.mirror_plot = False
        self.negative_plot = False
        self._drill_marks = 'full'

    @property
    def drill_marks(self):
        return self._drill_marks

    @drill_marks.setter
    def drill_marks(self, val):
        if val not in self._drill_marks_map:
            raise KiPlotConfigurationError("Unknown drill mark type: {}".format(val))
        self._drill_marks = val

    def config(self, outdir, options, layers):
        super().config(outdir, options, layers)
        self._drill_marks = self._drill_marks_map[self._drill_marks]


# Register it
BaseOutput.register('svg', SVG)
