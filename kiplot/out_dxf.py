from pcbnew import PLOT_FORMAT_DXF
from kiplot.out_any_layer import AnyLayer
from kiplot.drill_marks import DrillMarks
from kiplot.macros import macros, document, output_class  # noqa: F401


@output_class
class DXF(AnyLayer, DrillMarks):
    """
    DXF (Drawing Exchange Format)
    Exports the PCB to 2D mechanical EDA tools (like AutoCAD).
    This output is what you get from the File/Plot menu in pcbnew. """
    def __init__(self, name, type, description):
        AnyLayer.__init__(self, name, type, description)
        DrillMarks.__init__(self)
        self._plot_format = PLOT_FORMAT_DXF
        # Options
        with document:
            self.use_aux_axis_as_origin = False
            """ use the auxiliar axis as origin for coordinates """
            self.polygon_mode = True
            """ plot using the contour, instead of the center line """
            self.sketch_plot = False
            """ don't fill objects, just draw the outline """  # pragma: no cover

    def config(self, outdir, options, layers):
        AnyLayer.config(self, outdir, options, layers)
        DrillMarks.config(self)

    def _configure_plot_ctrl(self, po, output_dir):
        AnyLayer._configure_plot_ctrl(self, po, output_dir)
        po.SetDXFPlotPolygonMode(self.polygon_mode)
