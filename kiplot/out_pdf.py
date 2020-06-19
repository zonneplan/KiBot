from pcbnew import PLOT_FORMAT_PDF
from .out_base import BaseOutput
from .out_any_layer import AnyLayer
from .error import KiPlotConfigurationError


class PDF(AnyLayer):
    def __init__(self, name, type, description):
        super(PDF, self).__init__(name, type, description)
        self._plot_format = PLOT_FORMAT_PDF
        # Options
        self.line_width = 0.1
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
BaseOutput.register('pdf', PDF)
