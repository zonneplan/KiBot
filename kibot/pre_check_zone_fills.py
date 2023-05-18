# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from .error import (KiPlotConfigurationError)
from .macros import macros, pre_class  # noqa: F401


@pre_class
class Check_Zone_Fills(BasePreFlight):  # noqa: F821
    """ [boolean=false] Zones are filled before doing any operation involving PCB layers.
        The original PCB remains unchanged. If you need to abort when the zone fill
        creates significant changes to a layer use the CheckZoneFill internal template """
    def __init__(self, name, value):
        super().__init__(name, value)
        if not isinstance(value, bool):
            raise KiPlotConfigurationError('must be boolean')
        self._enabled = value

    def apply(self):
        BasePreFlight._set_option('check_zone_fills', self._enabled)  # noqa: F821
