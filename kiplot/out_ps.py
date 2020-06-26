from pcbnew import PLOT_FORMAT_POST
from .out_any_layer import AnyLayer
from .error import KiPlotConfigurationError
from kiplot.macros import macros, document, output_class  # noqa: F401


@output_class
class PS(AnyLayer):
    """ PS (Postscript)
        Exports the PCB to a format suitable for printing.
        This output is what you get from the File/Plot menu in pcbnew. """
    def __init__(self, name, type, description):
        super(PS, self).__init__(name, type, description)
        self._plot_format = PLOT_FORMAT_POST
        # Options
        with document:
            self.line_width = 0.15
            """ for objects without width [mm] """
            self.mirror_plot = False
            """ plot mirrored """
            self.negative_plot = False
            """ invert black and white """
            self.sketch_plot = False
            """ don't fill objects, just draw the outline """
            self.scaling = 1
            """ scale factor (0 means autoscaling)"""
            self._drill_marks = 'full'
            """ what to use to indicate the drill places, can be none, small or full (for real scale) """
            self.scale_adjust_x = 1.0
            """ fine grain adjust for the X scale (floating point multiplier) """
            self.scale_adjust_y = 1.0
            """ fine grain adjust for the Y scale (floating point multiplier) """
            self.width_adjust = 0
            """ this width factor is intended to compensate PS printers/plotters that do not strictly obey line width settings.
                Only used to plot pads and tracks """
            self.a4_output = True
            """ force A4 paper size """  # pragma: no cover

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
        po.SetWidthAdjust(self.width_adjust)
        po.SetFineScaleAdjustX(self.scale_adjust_x)
        po.SetFineScaleAdjustX(self.scale_adjust_y)
        po.SetA4Output(self.a4_output)
