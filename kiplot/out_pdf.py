from pcbnew import (PLOT_FORMAT_PDF, FromMM, ToMM)
from kiplot.out_any_layer import AnyLayer
from kiplot.drill_marks import DrillMarks
from kiplot.macros import macros, document, output_class  # noqa: F401


@output_class
class PDF(AnyLayer, DrillMarks):
    """ PDF (Portable Document Format)
        Exports the PCB to the most common exhange format. Suitable for printing.
        Note that this output isn't the best for documating your project.
        This output is what you get from the File/Plot menu in pcbnew. """
    def __init__(self, name, type, description):
        AnyLayer.__init__(self, name, type, description)
        DrillMarks.__init__(self)
        self._plot_format = PLOT_FORMAT_PDF
        # Options
        with document:
            self.line_width = 0.1
            """ [0.02,2] for objects without width [mm] """
            self.mirror_plot = False
            """ plot mirrored """
            self.negative_plot = False
            """ invert black and white """  # pragma: no cover

    def config(self, outdir, options, layers):
        AnyLayer.config(self, outdir, options, layers)
        DrillMarks.config(self)

    def _configure_plot_ctrl(self, po, output_dir):
        AnyLayer._configure_plot_ctrl(self, po, output_dir)
        DrillMarks._configure_plot_ctrl(self, po, output_dir)
        po.SetMirror(self.mirror_plot)
        po.SetLineWidth(FromMM(self.line_width))
        po.SetNegative(self.negative_plot)

    def read_vals_from_po(self, po):
        AnyLayer.read_vals_from_po(self, po)
        DrillMarks.read_vals_from_po(self, po)
        self.mirror_plot = po.GetMirror()
        self.line_width = ToMM(po.GetLineWidth())
        self.negative_plot = po.GetNegative()
