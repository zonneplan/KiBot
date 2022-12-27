# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from .gs import GS
from .out_base import VariantOptions
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class PCB_Variant_Options(VariantOptions):
    def __init__(self):
        with document:
            self.hide_excluded = False
            """ Hide components in the Fab layer that are marked as excluded by a variant.
                Affected by global options """
            self.output = GS.def_global_output
            """ *Filename for the output (%i=variant, %x=kicad_pcb) """
            self.copy_project = True
            """ Copy the KiCad project to the destination directory """
            self.title = ''
            """ Text used to replace the sheet title. %VALUE expansions are allowed.
                If it starts with `+` the text is concatenated """
        super().__init__()
        self._expand_id = 'variant'
        self._expand_ext = 'kicad_pcb'

    def get_targets(self, out_dir):
        return [self._parent.expand_filename(out_dir, self.output)]

    def run(self, output):
        super().run(output)
        self.filter_pcb_components(do_3D=True)
        self.set_title(self.title)
        logger.debug('Saving PCB to '+output)
        GS.board.Save(output)
        if self.copy_project:
            GS.copy_project(output)
        self.restore_title()
        self.unfilter_pcb_components(do_3D=True)


@output_class
class PCB_Variant(BaseOutput):  # noqa: F821
    """ PCB with variant generator
        Creates a copy of the PCB with all the filters and variants applied.
        This copy isn't intended for development.
        Is just a tweaked version of the original where you can look at the results. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = PCB_Variant_Options
            """ *[dict] Options for the `pcb_variant` output """
