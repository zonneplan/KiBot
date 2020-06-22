from pcbnew import (PLOT_FORMAT_GERBER)
from .out_base import (BaseOutput)
from .out_any_layer import (AnyLayer)
from .error import KiPlotConfigurationError
from kiplot.macros import macros, document


class Gerber(AnyLayer):
    def __init__(self, name, type, description):
        super(Gerber, self).__init__(name, type, description)
        self._plot_format = PLOT_FORMAT_GERBER
        # Options
        with document:
            self.use_aux_axis_as_origin = False
            """ Auxiliar origin """
            self.line_width = 0.1
            self.subtract_mask_from_silk = False
            self.use_protel_extensions = False
            self._gerber_precision = 4.6
            self.create_gerber_job_file = True
            self.use_gerber_x2_attributes = True
            self.use_gerber_net_attributes = True

    @property
    def gerber_precision(self):
        return self._gerber_precision

    @gerber_precision.setter
    def gerber_precision(self, val):
        if val != 4.5 and val != 4.6:
            raise KiPlotConfigurationError("`gerber_precision` must be 4.5 or 4.6")
        self._gerber_precision = val

    def _configure_plot_ctrl(self, po, output_dir):
        super()._configure_plot_ctrl(po, output_dir)
        po.SetUseGerberAttributes(True)
        po.SetSubtractMaskFromSilk(self.subtract_mask_from_silk)
        po.SetUseGerberProtelExtensions(self.use_protel_extensions)
        po.SetGerberPrecision(5 if self.gerber_precision == 4.5 else 6)
        po.SetCreateGerberJobFile(self.create_gerber_job_file)
        po.SetUseGerberAttributes(self.use_gerber_x2_attributes)
        po.SetIncludeGerberNetlistInfo(self.use_gerber_net_attributes)


# Register it
BaseOutput.register('gerber', Gerber)
