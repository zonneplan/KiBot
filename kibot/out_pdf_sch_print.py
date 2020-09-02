# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from tempfile import mkdtemp
from shutil import rmtree
from .gs import (GS)
from .kiplot import check_eeschema_do, exec_with_retry
from .misc import (CMD_EESCHEMA_DO, PDF_SCH_PRINT)
from .optionable import BaseOptions, Optionable
from .registrable import RegOutput
from .macros import macros, document, output_class  # noqa: F401
from .fil_base import BaseFilter, apply_fitted_filter
from . import log

logger = log.get_logger(__name__)


class PDF_Sch_PrintOptions(BaseOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ filename for the output PDF (%i=schematic %x=pdf) """
            self.variant = ''
            """ Board variant(s), used to determine which components are crossed. """
            self.dnf_filter = Optionable
            """ [string|list(string)=''] Name of the filter to mark components as not fitted.
                A short-cut to use for simple cases where a variant is an overkill """
        super().__init__()

    def config(self):
        super().config()
        self.variant = RegOutput.check_variant(self.variant)
        self.dnf_filter = BaseFilter.solve_filter(self.dnf_filter, 'dnf_filter')

    def run(self, output_dir, board):
        check_eeschema_do()
        if self.variant or self.dnf_filter:
            # Get the components list from the schematic
            comps = GS.sch.get_components()
            # Apply the filter
            apply_fitted_filter(comps, self.dnf_filter)
            # Apply the variant
            if self.variant:
                self.variant.filter(comps)
            # Save it to a temporal dir
            sch_dir = mkdtemp(prefix='tmp-kibot-pdf_sch_print-')
            fname = GS.sch.save_variant(sch_dir)
            sch_file = os.path.join(sch_dir, fname)
        else:
            sch_dir = None
            sch_file = GS.sch_file
        cmd = [CMD_EESCHEMA_DO, 'export', '--all_pages', '--file_format', 'pdf', sch_file, output_dir]
        if GS.debug_enabled:
            cmd.insert(1, '-vv')
            cmd.insert(1, '-r')
        ret = exec_with_retry(cmd)
        if ret:
            logger.error(CMD_EESCHEMA_DO+' returned %d', ret)
            exit(PDF_SCH_PRINT)
        if self.output:
            id = 'schematic'
            ext = 'pdf'
            cur = self.expand_filename_sch(output_dir, '%f.%x', id, ext)
            new = self.expand_filename_sch(output_dir, self.output, id, ext)
            logger.debug('Moving '+cur+' -> '+new)
            os.rename(cur, new)
        # Remove the temporal dir if needed
        if sch_dir:
            logger.debug('Removing temporal variant dir `{}`'.format(sch_dir))
            rmtree(sch_dir)


@output_class
class PDF_Sch_Print(BaseOutput):  # noqa: F821
    """ PDF Schematic Print (Portable Document Format)
        Exports the PCB to the most common exhange format. Suitable for printing.
        This is the main format to document your schematic.
        This output is what you get from the 'File/Print' menu in eeschema. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = PDF_Sch_PrintOptions
            """ [dict] Options for the `pdf_sch_print` output """
        self._sch_related = True
