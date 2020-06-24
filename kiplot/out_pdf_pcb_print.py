from subprocess import (call)
from .out_base import BaseOutput
from .pre_base import BasePreFlight
from .error import (KiPlotConfigurationError, PlotError)
from .kiplot import (check_script, GS)
from .misc import (CMD_PCBNEW_PRINT_LAYERS, URL_PCBNEW_PRINT_LAYERS, PDF_PCB_PRINT)
from kiplot.macros import macros, document  # noqa: F401
from . import log

logger = log.get_logger(__name__)


class PDFPcbPrint(BaseOutput):
    """ PDF PCB Print (Portable Document Format)
        Exports the PCB to the most common exhange format. Suitable for printing.
        This is the main format to document your PCB.
        This output is what you get from the 'File/Print' menu in pcbnew. """
    def __init__(self, name, type, description):
        super(PDFPcbPrint, self).__init__(name, type, description)
        # Options
        with document:
            self.output_name = 'pdf_pcb_print.pdf'
            """ filename for the output PDF """

    def config(self, outdir, options, layers):
        super().config(outdir, options, layers)
        # We need layers
        if not self._layers:
            raise KiPlotConfigurationError("Missing `layers` list")

    def run(self, output_dir, board):
        check_script(CMD_PCBNEW_PRINT_LAYERS, URL_PCBNEW_PRINT_LAYERS, '1.4.1')
        # Verify the inner layers
        layer_cnt = board.GetCopperLayerCount()
        for l in self._layers:
            # for inner layers, we can now check if the layer exists
            if l.is_inner:
                if l.id < 1 or l.id >= layer_cnt - 1:
                    raise PlotError("Inner layer `{}` is not valid for this board".format(l))
        cmd = [CMD_PCBNEW_PRINT_LAYERS, 'export', '--output_name', self.output_name]
        if BasePreFlight.get_option('check_zone_fills'):
            cmd.append('-f')
        cmd.extend([GS.pcb_file, output_dir])
        if GS.debug_enabled:
            cmd.insert(1, '-vv')
            cmd.insert(1, '-r')
        # Add the layers
        for l in self._layers:
            cmd.append(l.name)
        logger.debug('Executing: '+str(cmd))
        ret = call(cmd)
        if ret:
            logger.error(CMD_PCBNEW_PRINT_LAYERS+' returned %d', ret)
            exit(PDF_PCB_PRINT)


# Register it
BaseOutput.register('pdf_pcb_print', PDFPcbPrint)
