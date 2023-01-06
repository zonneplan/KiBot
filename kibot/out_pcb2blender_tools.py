# -*- coding: utf-8 -*-
# Copyright (c) 2023 Salvador E. Tropea
# Copyright (c) 2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Some code is adapted from: https://github.com/30350n/pcb2blender
import json
import os
import struct
from pcbnew import B_Paste, F_Paste
from .gs import GS
from .misc import MOD_THROUGH_HOLE, MOD_SMD, UI_VIRTUAL
from .out_base import VariantOptions
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class PCB2Blender_ToolsOptions(VariantOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i=pcb2blender, %x=pcb3d) """
            self.board_bounds_create = True
            """ Create the file that informs the size of the used PCB area.
                This is the bounding box reported by KiCad for the PCB edge with 1 mm of margin """
            self.board_bounds_dir = 'layers'
            """ Sub-directory where the bounds file is stored """
            self.board_bounds_file = 'bounds'
            """ Name of the bounds file """
            self.pads_info_create = True
            """ Create the files containing the PCB pads information """
            self.pads_info_dir = 'pads'
            """ Sub-directory where the pads info files are stored """
            self.stackup_create = False
            """ Create a JSON file containing the board stackup """
            self.stackup_file = 'board.yaml'
            """ Name for the stackup file """
            self.stackup_dir = '.'
            """ Directory for the stackup file """
        super().__init__()
        self._expand_id = 'pcb2blender'
        self._expand_ext = 'pcb3d'

    def do_board_bounds(self, dir_name):
        if not self.board_bounds_create:
            return
        dir_name = os.path.join(dir_name, self.board_bounds_dir)
        os.makedirs(dir_name, exist_ok=True)
        fname = os.path.join(dir_name, self.board_bounds_file)
        # PCB bounding box using the PCB edge, converted to mm
        bounds = tuple(map(GS.to_mm, GS.board.ComputeBoundingBox(aBoardEdgesOnly=True).getWxRect()))
        # Apply 1 mm margin (x, y, w, h)
        bounds = (bounds[0]-1, bounds[1]-1, bounds[2]+2, bounds[3]+2)
        with open(fname, 'wb') as f:
            # Four big endian float numbers
            f.write(struct.pack("!ffff", *bounds))

    @staticmethod
    def is_not_virtual_ki6(m):
        return bool(m.GetAttributes() & (MOD_THROUGH_HOLE | MOD_SMD))

    @staticmethod
    def is_not_virtual_ki5(m):
        return bool(m.GetAttributes() != UI_VIRTUAL)

    def do_pads_info(self, dir_name):
        if not self.pads_info_create:
            return
        dir_name = os.path.join(dir_name, self.pads_info_dir)
        os.makedirs(dir_name, exist_ok=True)
        is_not_virtual = self.is_not_virtual_ki5 if GS.ki5 else self.is_not_virtual_ki6
        for i, footprint in enumerate(GS.get_modules()):
            has_model = len(footprint.Models()) > 0
            is_tht_or_smd = is_not_virtual(footprint)
            value = footprint.GetValue()
            reference = footprint.GetReference()
            for j, pad in enumerate(footprint.Pads()):
                name = os.path.join(dir_name, "{}_{}_{}_{}".format(value, reference, i, j))
                is_flipped = pad.IsFlipped()
                has_paste = pad.IsOnLayer(B_Paste if is_flipped else F_Paste)
                with open(name, 'wb') as f:
                    f.write(struct.pack("!ff????BBffffBff",
                                        *map(GS.to_mm, pad.GetPosition()),
                                        is_flipped,
                                        has_model,
                                        is_tht_or_smd,
                                        has_paste,
                                        pad.GetAttribute(),
                                        pad.GetShape(),
                                        *map(GS.to_mm, pad.GetSize()),
                                        pad.GetOrientationRadians(),
                                        pad.GetRoundRectRadiusRatio(),
                                        pad.GetDrillShape(),
                                        *map(GS.to_mm, pad.GetDrillSize())))

    def do_stackup(self, dir_name):
        if not self.stackup_create or (not GS.global_pcb_finish and not GS.stackup):
            return
        dir_name = os.path.join(dir_name, self.stackup_dir)
        os.makedirs(dir_name, exist_ok=True)
        fname = os.path.join(dir_name, self.stackup_file)
        # Create the board_info
        board_info = {}
        if GS.global_pcb_finish:
            board_info['copper_finish'] = GS.global_pcb_finish
        if GS.stackup:
            layers_parsed = []
            for la in GS.stackup:
                parsed_layer = {'name': la.name, 'type': la.type}
                if la.color is not None:
                    parsed_layer['color'] = la.color
                if la.thickness is not None:
                    parsed_layer['thickness'] = la.thickness/1000
                layers_parsed.append(parsed_layer)
            board_info['stackup'] = layers_parsed
        with open(fname, 'wt') as f:
            json.dump(board_info, f, indent=3)

    def run(self, output):
        super().run(output)
        dir_name = os.path.dirname(output)
        self.filter_pcb_components(do_3D=True)
        self.do_board_bounds(dir_name)
        self.do_pads_info(dir_name)
        self.do_stackup(dir_name)
        self.unfilter_pcb_components(do_3D=True)

    def get_targets(self, out_dir):
        files = []
        if self.board_bounds_create:
            files.append(os.path.join(out_dir, self.board_bounds_dir, self.board_bounds_file))
        if self.pads_info_create:
            dir_name = os.path.join(out_dir, self.pads_info_dir)
            for i, footprint in enumerate(GS.get_modules()):
                value = footprint.GetValue()
                reference = footprint.GetReference()
                for j in range(len(footprint.Pads())):
                    files.append(os.path.join(dir_name, "{}_{}_{}_{}".format(value, reference, i, j)))
        return files


@output_class
class PCB2Blender_Tools(BaseOutput):  # noqa: F821
    """ PCB2Blender Tools
        A bunch of tools used to generate PCB3D files used to export PCBs to Blender.
        Blender is the most important free software 3D render package.
        The PCB3D file format is used by the PCB2Blender project (https://github.com/30350n/pcb2blender)
        to import KiCad PCBs in Blender.
        You need to install a Blender plug-in to load PCB3D files.
        The tools in this output are used by internal templates used to generate PCB3D files. """
    def __init__(self):
        super().__init__()
        self._category = 'PCB/3D'
        with document:
            self.options = PCB2Blender_ToolsOptions
            """ *[dict] Options for the `pcb2blender_tools` output """
