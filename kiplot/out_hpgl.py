from pcbnew import (PLOT_FORMAT_HPGL)
from .out_base import (BaseOutput)
from .out_any_layer import (AnyLayer)
from .error import KiPlotConfigurationError


class HPGL(AnyLayer):
    def __init__(self, name, type, description):
        super(HPGL, self).__init__(name, type, description)
        self._plot_format = PLOT_FORMAT_HPGL
        # Options
        self.mirror_plot = False
        self.sketch_plot = True
        self.scaling = 0
        self._drill_marks = 'full'
        self.pen_width = 0.5

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
