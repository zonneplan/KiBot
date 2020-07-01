from pcbnew import PLOT_FORMAT_HPGL
from kiplot.out_any_layer import AnyLayer
from kiplot.drill_marks import DrillMarks
from kiplot.macros import macros, document, output_class  # noqa: F401


@output_class
class HPGL(AnyLayer, DrillMarks):
    """ HPGL (Hewlett & Packard Graphics Language)
        Exports the PCB for plotters and laser printers.
        This output is what you get from the File/Plot menu in pcbnew. """
    def __init__(self, name, type, description):
        AnyLayer.__init__(self, name, type, description)
        DrillMarks.__init__(self)
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
        super()._configure_plot_ctrl(po, output_dir)
        po.SetHPGLPenDiameter(self.pen_width)
        po.SetHPGLPenNum(self.pen_number)
        po.SetHPGLPenSpeed(self.pen_speed)
