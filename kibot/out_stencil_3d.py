# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - from: KiKit
    role: mandatory
  - name: OpenSCAD
    url: https://openscad.org/
    url_down: https://openscad.org/downloads.html
    command: openscad
    debian: openscad
    arch: openscad
    role: mandatory
"""
from .gs import GS
from .macros import macros, document, output_class  # noqa: F401
from .out_any_stencil import Stencil_Options
from . import log

logger = log.get_logger()


class Stencil_3D_Options(Stencil_Options):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i='stencil_3d_top'|'stencil_3d_bottom'|'stencil_3d_edge',
                 %x='stl'|'scad'|'dxf') """
            self.thickness = 0.15
            """ *Stencil thickness [mm]. Defines amount of paste dispensed """
            self.framewidth = 1
            """ Register frame width """
            self.frame_width = None
            """ {framewidth} """
            self.frameclearance = 0
            """ Clearance for the stencil register [mm] """
            self.frame_clearance = None
            """ {frameclearance} """
            self.enlargeholes = 0
            """ Enlarge pad holes by x mm """
            self.enlarge_holes = None
            """ {enlarge_holes} """
        super().__init__()
        self.add_to_doc('include_scad', 'Note that this also includes the DXF files')

    def get_targets(self, out_dir):
        do_top, do_bottom = self.solve_sides()
        files = []
        # The edge is needed by any of the OpenSCAD files
        if (do_top or do_bottom) and self.include_scad:
            files.append(self.expand_name('stencil_3d_edge', 'dxf', out_dir))
        # Top side
        if do_top:
            files.append(self.expand_name('stencil_3d_top', 'stl', out_dir))
            if self.include_scad:
                files.append(self.expand_name('stencil_3d_top', 'dxf', out_dir))
                files.append(self.expand_name('stencil_3d_top', 'scad', out_dir))
        # Bottom side
        if do_bottom:
            files.append(self.expand_name('stencil_3d_bottom', 'stl', out_dir))
            if self.include_scad:
                files.append(self.expand_name('stencil_3d_bottom', 'dxf', out_dir))
                files.append(self.expand_name('stencil_3d_bottom', 'scad', out_dir))
        return files

    def create_cmd(self, cmd_kikit):
        cmd = [cmd_kikit, 'stencil', 'createprinted',
               '--thickness', str(self.thickness),
               '--framewidth', str(self.framewidth),
               '--pcbthickness', str(self.pcbthickness)]
        if self.cutout:
            cmd.extend(['--coutout', self.cutout])
        if self.frameclearance:
            cmd.extend(['--frameclearance', str(self.frameclearance)])
        if self.enlargeholes:
            cmd.extend(['--enlargeholes', str(self.enlargeholes)])
        return cmd

    def move_outputs(self, tmp, prj_name, do_top, do_bottom):
        replacements = {}
        # The edge is needed by any of the OpenSCAD files
        if (do_top or do_bottom) and self.include_scad:
            self.move_output(tmp, prj_name+'-EdgeCuts.dxf', 'stencil_3d_edge', 'dxf', replacements)
        # Top side
        if do_top:
            self.move_output(tmp, 'topStencil.stl', 'stencil_3d_top', 'stl')
            if self.include_scad:
                self.move_output(tmp, prj_name+'-PasteTop.dxf', 'stencil_3d_top', 'dxf', replacements)
                self.move_output(tmp, 'topStencil.scad', 'stencil_3d_top', 'scad', replacements, patch=True)
        # Bottom side
        if do_bottom:
            self.move_output(tmp, 'bottomStencil.stl', 'stencil_3d_bottom', 'stl')
            if self.include_scad:
                self.move_output(tmp, prj_name+'-PasteBottom.dxf', 'stencil_3d_bottom', 'dxf', replacements)
                self.move_output(tmp, 'bottomStencil.scad', 'stencil_3d_bottom', 'scad', replacements, patch=True)


@output_class
class Stencil_3D(BaseOutput):  # noqa: F821
    """ 3D Printed Stencils
        Creates a 3D self-registering model of a stencil you can easily print on
        SLA printer, you can use it to apply solder paste to your PCB.
        These stencils are quick solution when you urgently need a stencil but probably
        they don't last long and might come with imperfections.
        It currently uses KiKit, so please read
        [KiKit docs](https://github.com/yaqwsx/KiKit/blob/master/doc/stencil.md).
        Note that we don't implement `--ignore` option, you should use a variant for this """
    def __init__(self):
        super().__init__()
        with document:
            self.options = Stencil_3D_Options
            """ *[dict] Options for the `stencil_3d` output """
