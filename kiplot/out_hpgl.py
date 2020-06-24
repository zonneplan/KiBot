from pcbnew import (PLOT_FORMAT_HPGL)
from .out_base import (BaseOutput)
from .out_any_layer import (AnyLayer)
from .error import KiPlotConfigurationError
from kiplot.macros import macros, document  # noqa: F401


class HPGL(AnyLayer):
    """ HPGL (Hewlett & Packard Graphics Language)
        Exports the PCB for plotters and laser printers.
        This output is what you get from the File/Plot menu in pcbnew. """
    def __init__(self, name, type, description):
        super(HPGL, self).__init__(name, type, description)
        self._plot_format = PLOT_FORMAT_HPGL
        # Options
        with document:
            self.mirror_plot = False
            """ plot mirrored """
            self.sketch_plot = False
            """ don't fill objects, just draw the outline """
            self.scaling = 0
            """ scale factor """
            self._drill_marks = 'full'
            """ what to use to indicate the drill places, can be none, small or full (for real scale) """
            self.pen_width = 0.5
            """ default trace width """
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
        po.SetHPGLPenDiameter(self.pen_width)


# Register it
BaseOutput.register('hpgl', HPGL)
