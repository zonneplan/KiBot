from pcbnew import PLOT_FORMAT_SVG
from kiplot.out_any_layer import AnyLayer
from kiplot.drill_marks import DrillMarks
from kiplot.macros import macros, document, output_class  # noqa: F401


@output_class
class SVG(AnyLayer, DrillMarks):
    """ SVG (Scalable Vector Graphics)
        Exports the PCB to a format suitable for 2D graphics software.
        Unlike bitmaps SVG drawings can be scaled without losing resolution.
        This output is what you get from the File/Plot menu in pcbnew. """
    def __init__(self, name, type, description):
        AnyLayer.__init__(self, name, type, description)
        DrillMarks.__init__(self)
        self._plot_format = PLOT_FORMAT_SVG
        # Options
        with document:
            self.line_width = 0.25
            """ for objects without width [mm] """
            self.mirror_plot = False
            """ plot mirrored """
            self.negative_plot = False
            """ invert black and white """  # pragma: no cover

    def config(self, outdir, options, layers):
        AnyLayer.config(self, outdir, options, layers)
        DrillMarks.config(self)
