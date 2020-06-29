from pcbnew import PLOT_FORMAT_POST
from kiplot.out_any_layer import AnyLayer
from kiplot.drill_marks import DrillMarks
from kiplot.macros import macros, document, output_class  # noqa: F401


@output_class
class PS(AnyLayer, DrillMarks):
    """ PS (Postscript)
        Exports the PCB to a format suitable for printing.
        This output is what you get from the File/Plot menu in pcbnew. """
    def __init__(self, name, type, description):
        AnyLayer.__init__(self, name, type, description)
        DrillMarks.__init__(self)
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
            self.scale_adjust_x = 1.0
            """ fine grain adjust for the X scale (floating point multiplier) """
            self.scale_adjust_y = 1.0
            """ fine grain adjust for the Y scale (floating point multiplier) """
            self.width_adjust = 0
            """ this width factor is intended to compensate PS printers/plotters that do not strictly obey line width settings.
                Only used to plot pads and tracks """
            self.a4_output = True
            """ force A4 paper size """  # pragma: no cover

    def config(self, outdir, options, layers):
        AnyLayer.config(self, outdir, options, layers)
        DrillMarks.config(self)

    def _configure_plot_ctrl(self, po, output_dir):
        super()._configure_plot_ctrl(po, output_dir)
        po.SetWidthAdjust(self.width_adjust)
        po.SetFineScaleAdjustX(self.scale_adjust_x)
        po.SetFineScaleAdjustX(self.scale_adjust_y)
        po.SetA4Output(self.a4_output)
