# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024 Salvador E. Tropea
# Copyright (c) 2022-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
import pcbnew
from .gs import GS
from .kiplot import load_board
from .macros import macros, document, pre_class  # noqa: F401


@pre_class
class Fill_Zones(BasePreFlight):  # noqa: F821
    def __init__(self):
        super().__init__()
        self._pcb_related = True
        with document:
            self.fill_zones = False
            """ [boolean=false] Fill all zones again and save the PCB """

    def apply(self):
        load_board()
        pcbnew.ZONE_FILLER(GS.board).Fill(GS.board.Zones())
        GS.make_bkp(GS.pcb_file)
        # KiCad likes to write the project every time we save the PCB
        # But KiCad doesn't read the exclusions, so they get lost
        # As a workaround we restore the project, there is no need to change it
        prj = GS.read_pro()
        GS.board.Save(GS.pcb_file)
        GS.write_pro(prj)
