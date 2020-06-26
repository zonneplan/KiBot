from pcbnew import PLOT_FORMAT_SVG
from .out_any_layer import AnyLayer
from .error import KiPlotConfigurationError
from kiplot.macros import macros, document, output_class  # noqa: F401


@output_class
class SVG(AnyLayer):
    """ SVG (Scalable Vector Graphics)
        Exports the PCB to a format suitable for 2D graphics software.
        Unlike bitmaps SVG drawings can be scaled without losing resolution.
        This output is what you get from the File/Plot menu in pcbnew. """
    def __init__(self, name, type, description):
        super(SVG, self).__init__(name, type, description)
        self._plot_format = PLOT_FORMAT_SVG
        # Options
        with document:
            self.line_width = 0.25
            """ for objects without width [mm] """
            self.mirror_plot = False
            """ plot mirrored """
            self.negative_plot = False
            """ invert black and white """
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

    def config(self, outdir, options, layers):
        super().config(outdir, options, layers)
        self._drill_marks = self._drill_marks_map[self._drill_marks]
