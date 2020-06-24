from pcbnew import PLOT_FORMAT_PDF
from .out_base import BaseOutput
from .out_any_layer import AnyLayer
from .error import KiPlotConfigurationError
from kiplot.macros import macros, document  # noqa: F401


class PDF(AnyLayer):
    """ PDF (Portable Document Format)
        Exports the PCB to the most common exhange format. Suitable for printing.
        Note that this output isn't the best for documating your project.
        This output is what you get from the File/Plot menu in pcbnew. """
    def __init__(self, name, type, description):
        super(PDF, self).__init__(name, type, description)
        self._plot_format = PLOT_FORMAT_PDF
        # Options
        with document:
            self.line_width = 0.1
            """ for objects without width [mm] """
            self.mirror_plot = False
            """ plot mirrored """
            self.negative_plot = False
            """ invert black and white """
            self._drill_marks = 'full'
            """ what to use to indicate the drill places, can be none, small or full (for real scale) """

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
