# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from .gs import GS
from .out_base import VariantOptions
from .macros import macros, document, output_class  # noqa: F401


class Sch_Variant_Options(VariantOptions):
    def __init__(self):
        super().__init__()

    def run(self, output_dir, board):
        super().run(output_dir, board)
        # Create the schematic
        GS.sch.save_variant(output_dir)


@output_class
class Sch_Variant(BaseOutput):  # noqa: F821
    """ Schematic with variant generator
        Creates a copy of the schematic with all the filters and variants applied.
        This copy isn't intended for development.
        Is just a tweaked version of the original where you can look at the results. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = Sch_Variant_Options
            """ [dict] Options for the `sch_variant` output """
        self._sch_related = True
