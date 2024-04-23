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
    """ [string|list(string)=''] Updates footprints from the libs, you must provide one or more references to be updated.
        This is useful to replace logos using freshly created versions """
    def __init__(self, name, value):
        super().__init__(name, value)
        self._pcb_related = True

    def config(self):
        if not isinstance(self._value, list) and not isinstance(self._value, str):
            raise KiPlotConfigurationError('must be string or list of strings')
        if isinstance(self._value, list) and any((not isinstance(x, str) for x in self._value)):
            raise KiPlotConfigurationError('all items in the list must be strings')
        self._refs = Optionable.force_list(self._value)
        if not self._refs:
            raise KiPlotConfigurationError('nothing to update')

    def get_example():
        """ Returns a YAML value for the example config """
        return "QR1, QR2"

    def apply(self):
        replace_footprints(GS.pcb_file, {k: None for k in self._refs}, logger)
