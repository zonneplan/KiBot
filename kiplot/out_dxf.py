from pcbnew import PLOT_FORMAT_DXF
from .error import KiPlotConfigurationError
from .out_any_layer import (AnyLayer)
from kiplot.macros import macros, document, output_class  # noqa: F401


@output_class
class DXF(AnyLayer):
    """
    DXF (Drawing Exchange Format)
    Exports the PCB to 2D mechanical EDA tools (like AutoCAD).
    This output is what you get from the File/Plot menu in pcbnew. """
    def __init__(self, name, type, description):
        super(DXF, self).__init__(name, type, description)
        self._plot_format = PLOT_FORMAT_DXF
        # Options
        with document:
            self.use_aux_axis_as_origin = False
            """ use the auxiliar axis as origin for coordinates """
            self._drill_marks = 'full'
            """ drill_marks what to use to indicate the drill places, can be none, small or full (for real scale) """
            self.polygon_mode = True
            """ plot using the contour, instead of the center line """
            self.sketch_plot = False
            """ don't fill objects, just draw the outline """  # pragma: no cover

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

    def _configure_plot_ctrl(self, po, output_dir):
        super()._configure_plot_ctrl(po, output_dir)
        po.SetDXFPlotPolygonMode(self.polygon_mode)
