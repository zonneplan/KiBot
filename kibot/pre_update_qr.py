# -*- coding: utf-8 -*-
# Copyright (c) 2020-2024 Salvador E. Tropea
# Copyright (c) 2020-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from .macros import macros, document, pre_class  # noqa: F401
from .registrable import RegOutput
from .log import get_logger

logger = get_logger(__name__)


@pre_class
class Update_QR(BasePreFlight):  # noqa: F821
    """ Update QR
        Update the QR codes.
        Complements the `qr_lib` output.
        The KiCad 6 files and the KiCad 5 PCB needs manual update, generating a new library isn't enough """
    def __init__(self):
        super().__init__()
        self._sch_related = True
        self._pcb_related = True
        with document:
            self.update_qr = False
            """ Enable this preflight """

    def run(self):
        for o in RegOutput.get_outputs():
            if o.type == 'qr_lib':
                BasePreFlight.insert_target(o)  # noqa: F821
                o._update_mode = True
                logger.debug('Making {} prioritary'.format(o))
