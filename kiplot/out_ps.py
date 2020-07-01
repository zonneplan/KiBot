from pcbnew import (PLOT_FORMAT_POST, SKETCH, FILLED, FromMM, ToMM)
from kiplot.misc import AUTO_SCALE
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
            """ [0.02,2] for objects without width [mm] """
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
        AnyLayer._configure_plot_ctrl(self, po, output_dir)
        DrillMarks._configure_plot_ctrl(self, po, output_dir)
        po.SetWidthAdjust(self.width_adjust)
        po.SetFineScaleAdjustX(self.scale_adjust_x)
        po.SetFineScaleAdjustX(self.scale_adjust_y)
        po.SetA4Output(self.a4_output)
        po.SetPlotMode(SKETCH if self.sketch_plot else FILLED)
        po.SetLineWidth(FromMM(self.line_width))
        po.SetNegative(self.negative_plot)
        po.SetMirror(self.mirror_plot)
        # Scaling/Autoscale
        if self.scaling == AUTO_SCALE:
            po.SetAutoScale(True)
            po.SetScale(1)
        else:
            po.SetAutoScale(False)
            po.SetScale(self.scaling)

    def read_vals_from_po(self, po):
        AnyLayer.read_vals_from_po(self, po)
        DrillMarks.read_vals_from_po(self, po)
        self.width_adjust = po.GetWidthAdjust()
        self.scale_adjust_x = po.GetFineScaleAdjustX()
        self.scale_adjust_y = po.GetFineScaleAdjustX()
        self.a4_output = po.GetA4Output()
        self.sketch_plot = po.GetPlotMode() == SKETCH
        self.line_width = ToMM(po.GetLineWidth())
        self.negative_plot = po.GetNegative()
        self.mirror_plot = po.GetMirror()
        # scaleselection
        if po.GetAutoScale():
            self.scaling = AUTO_SCALE
        else:
            self.scaling = po.GetScale()
