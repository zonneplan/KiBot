from pcbnew import PLOT_FORMAT_POST
from .out_base import BaseOutput
from .out_any_layer import AnyLayer
from .error import KiPlotConfigurationError


class PS(AnyLayer):
    def __init__(self, name, type, description):
        super(PS, self).__init__(name, type, description)
        self._plot_format = PLOT_FORMAT_POST
        # Options
        self.line_width = 0.15
        self.mirror_plot = False
        self.negative_plot = False
        self.sketch_plot = True
        self.scaling = 2
        self._drill_marks = 'full'
        self.scale_adjust_x = 1.0
        self.scale_adjust_y = 1.0
        self.width_adjust = 0
        self.a4_output = True

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


# Register it
BaseOutput.register('ps', PS)
