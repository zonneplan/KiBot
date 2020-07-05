from pcbnew import (PLOT_FORMAT_HPGL, SKETCH, FILLED)
from kiplot.misc import AUTO_SCALE
from kiplot.out_any_layer import AnyLayer
from kiplot.drill_marks import DrillMarks
from kiplot.macros import macros, document, output_class  # noqa: F401


@output_class
class HPGL(AnyLayer, DrillMarks):
    """ HPGL (Hewlett & Packard Graphics Language)
        Exports the PCB for plotters and laser printers.
        This output is what you get from the File/Plot menu in pcbnew. """
    def __init__(self, name, type, description):
        super().__init__(name, type, description)
        self._plot_format = PLOT_FORMAT_HPGL
        # Options
        with document:
            self.mirror_plot = False
            """ plot mirrored """
            self.sketch_plot = False
            """ don't fill objects, just draw the outline """
            self.scaling = 0
            """ scale factor (0 means autoscaling) """
            self.pen_number = 1
            """ [1,16] pen number """
            self.pen_speed = 20
            """ [1,99] pen speed """
            self.pen_width = 15
            """ [0,100] pen diameter in MILS, useful to fill areas. However, it is in mm in HPGL files """  # pragma: no cover

    def config(self, outdir, options, layers):
        AnyLayer.config(self, outdir, options, layers)
        DrillMarks.config(self)

    def _configure_plot_ctrl(self, po, output_dir):
        AnyLayer._configure_plot_ctrl(self, po, output_dir)
        DrillMarks._configure_plot_ctrl(self, po, output_dir)
        po.SetHPGLPenDiameter(self.pen_width)
        po.SetHPGLPenNum(self.pen_number)
        po.SetHPGLPenSpeed(self.pen_speed)
        po.SetPlotMode(SKETCH if self.sketch_plot else FILLED)
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
        self.pen_width = po.GetHPGLPenDiameter()
        self.pen_number = po.GetHPGLPenNum()
        self.pen_speed = po.GetHPGLPenSpeed()
        self.sketch_plot = po.GetPlotMode() == SKETCH
        self.mirror_plot = po.GetMirror()
        # scaleselection
        if po.GetAutoScale():
            self.scaling = AUTO_SCALE
        else:
            self.scaling = po.GetScale()
