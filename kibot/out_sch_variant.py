# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from .error import KiPlotConfigurationError
from .gs import GS
from .optionable import BaseOptions
from .registrable import RegOutput
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger(__name__)


class Sch_Variant_Options(BaseOptions):
    def __init__(self):
        with document:
            self.variant = ''
            """ Board variant(s) to apply """
        super().__init__()

    def config(self):
        super().config()
        if self.variant:
            if not RegOutput.is_variant(self.variant):
                raise KiPlotConfigurationError("Unknown variant name `{}`".format(self.variant))
            self.variant = RegOutput.get_variant(self.variant)
        else:
            self.variant = None

    def run(self, output_dir, board):
        if self.variant:
            # Get the components list from the schematic
            comps = GS.sch.get_components()
            # Apply the variant
            self.variant.filter(comps)
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
