# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from tempfile import NamedTemporaryFile
from .pre_base import BasePreFlight
from .error import (KiPlotConfigurationError)
from .gs import (GS)
from .kiplot import check_script, exec_with_retry
from .misc import (CMD_PCBNEW_PRINT_LAYERS, URL_PCBNEW_PRINT_LAYERS, PDF_PCB_PRINT)
from .out_base import VariantOptions
from .macros import macros, document, output_class  # noqa: F401
from .layer import Layer
from . import log

logger = log.get_logger(__name__)


class PDF_Pcb_PrintOptions(VariantOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ filename for the output PDF (%i=layers, %x=pdf)"""
            self.output_name = None
            """ {output} """
        super().__init__()

    def filter_components(self, board):
        if not self._comps:
            return GS.pcb_file
        comps_hash = self.get_refs_hash()
        self.cross_modules(board, comps_hash)
        # Save the PCB to a temporal file
        with NamedTemporaryFile(mode='w', suffix='.kicad_pcb', delete=False) as f:
            fname = f.name
        logger.debug('Storing filtered PCB to `{}`'.format(fname))
        GS.board.Save(fname)
        self.uncross_modules(board, comps_hash)
        return fname

    def run(self, output_dir, board, layers):
        super().run(board, layers)
        check_script(CMD_PCBNEW_PRINT_LAYERS, URL_PCBNEW_PRINT_LAYERS, '1.4.1')
        layers = Layer.solve(layers)
        # Output file name
        id = '+'.join([la.suffix for la in layers])
        output = self.expand_filename(output_dir, self.output, id, 'pdf')
        cmd = [CMD_PCBNEW_PRINT_LAYERS, 'export', '--output_name', output]
        if BasePreFlight.get_option('check_zone_fills'):
            cmd.append('-f')
        board_name = self.filter_components(board)
        cmd.extend([board_name, output_dir])
        if GS.debug_enabled:
            cmd.insert(1, '-vv')
            cmd.insert(1, '-r')
        # Add the layers
        cmd.extend([la.layer for la in layers])
        # Execute it
        ret = exec_with_retry(cmd)
        # Remove the temporal PCB
        if board_name != GS.pcb_file:
            os.remove(board_name)
        if ret:  # pragma: no cover
            # We check all the arguments, we even load the PCB
            # A fail here isn't easy to reproduce
            logger.error(CMD_PCBNEW_PRINT_LAYERS+' returned %d', ret)
            exit(PDF_PCB_PRINT)


@output_class
class PDF_Pcb_Print(BaseOutput):  # noqa: F821
    """ PDF PCB Print (Portable Document Format)
        Exports the PCB to the most common exhange format. Suitable for printing.
        This is the main format to document your PCB.
        This output is what you get from the 'File/Print' menu in pcbnew. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = PDF_Pcb_PrintOptions
            """ [dict] Options for the `pdf_pcb_print` output """
            self.layers = Layer
            """ [list(dict)|list(string)|string] [all,selected,copper,technical,user]
                List of PCB layers to include in the PDF """

    def config(self):
        super().config()
        # We need layers
        if isinstance(self.layers, type):
            raise KiPlotConfigurationError("Missing `layers` list")

    def run(self, output_dir, board):
        self.options.run(output_dir, board, self.layers)
