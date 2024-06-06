# -*- coding: utf-8 -*-
# Copyright (c) 2020-2024 Salvador E. Tropea
# Copyright (c) 2020-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from .gs import GS
from .error import KiPlotConfigurationError
from .kicad.pcb import replace_footprints
from .optionable import Optionable
from .macros import macros, document, pre_class  # noqa: F401
from .log import get_logger

logger = get_logger(__name__)


@pre_class
class Update_Footprint(BasePreFlight):  # noqa: F821
    def __init__(self):
        super().__init__()
        self._pcb_related = True
        with document:
            self.update_footprint = ''
            """ [string|list(string)=''] Updates footprints from the libs, you must provide one or more references to be
                updated. This is useful to replace logos using freshly created versions """

    def config(self, parent):
        super().config(parent)
        if isinstance(self.update_footprint, list) and any((not isinstance(x, str) for x in self.update_footprint)):
            raise KiPlotConfigurationError('all items in the list must be strings')
        self._refs = Optionable.force_list(self.update_footprint)
        if not self._refs:
            raise KiPlotConfigurationError('nothing to update')

    def get_example():
        """ Returns a YAML value for the example config """
        return "QR1, QR2"

    def apply(self):
        replace_footprints(GS.pcb_file, {k: None for k in self._refs}, logger)
