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


class Stencil_For_Jig_Options(Stencil_Options):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i='stencil_for_jig_top'|'stencil_for_jig_bottom',
                 %x='stl'|'scad'|'gbp'|'gtp'|'gbrjob') """
            self.jigthickness = 3
            """ *Jig thickness [mm] """
            self.jig_thickness = None
            """ {jigthickness} """
            self.registerborderouter = 3
            """ Outer register border [mm] """
            self.register_border_outer = None
            """ {registerborderouter} """
            self.registerborderinner = 1
            """ Inner register border [mm] """
            self.register_border_inner = None
            """ {registerborderinner} """
            self.tolerance = 0.05
            """ Enlarges the register by the tolerance value [mm] """
            self.jigwidth = 100
            """ *Jig frame width [mm] """
            self.jig_width = None
            """ {jigwidth} """
            self.jigheight = 100
            """ *Jig frame height [mm] """
            self.jig_height = None
            """ {jigheight} """
        super().__init__()

    def get_targets(self, out_dir):
        do_top, do_bottom = self.solve_sides()
        files = []
        # Top side
        if do_top:
            files.append(self.expand_name('stencil_for_jig_top', 'gtp', out_dir))
            files.append(self.expand_name('stencil_for_jig_top', 'stl', out_dir))
            if self.include_scad:
                files.append(self.expand_name('stencil_for_jig_top', 'scad', out_dir))
        # Bottom side
        if do_bottom:
            files.append(self.expand_name('stencil_for_jig_bottom', 'gtp', out_dir))
            files.append(self.expand_name('stencil_for_jig_bottom', 'stl', out_dir))
            if self.include_scad:
                files.append(self.expand_name('stencil_for_jig_bottom', 'scad', out_dir))
        if do_top and do_bottom:
            files.append(self.expand_name('stencil_for_jig', 'gbrjob', out_dir))
        return files

    def create_cmd(self, cmd_kikit):
        cmd = [cmd_kikit, 'stencil', 'create',
               '--jigsize', str(self.jigwidth), str(self.jigheight),
               '--jigthickness', str(self.jigthickness),
               '--pcbthickness', str(self.pcbthickness),
               '--registerborder', str(self.registerborderouter), str(self.registerborderinner),
               '--tolerance', str(self.tolerance)]
        if self.cutout:
            cmd.extend(['--coutout', self.cutout])
        return cmd

    def move_outputs(self, tmp, prj_name, do_top, do_bottom):
        replacements = {}
        # Top side
        if do_top:
            self.move_output(tmp, 'gerber/stencil-PasteTop.gtp', 'stencil_for_jig_top', 'gtp', replacements, relative=True)
            self.move_output(tmp, 'topRegister.stl', 'stencil_for_jig_top', 'stl')
            if self.include_scad:
                self.move_output(tmp, 'topRegister.scad', 'stencil_for_jig_top', 'scad')
        # Bottom side
        if do_bottom:
            self.move_output(tmp, 'gerber/stencil-PasteBottom.gbp', 'stencil_for_jig_bottom', 'gbp', replacements,
                             relative=True)
            self.move_output(tmp, 'bottomRegister.stl', 'stencil_for_jig_bottom', 'stl')
            if self.include_scad:
                self.move_output(tmp, 'bottomRegister.scad', 'stencil_for_jig_bottom', 'scad')
        if do_top and do_bottom:
            self.move_output(tmp, 'gerber/stencil.gbrjob', 'stencil_for_jig', 'gbrjob', replacements, patch=True)


@output_class
class Stencil_For_Jig(BaseOutput):  # noqa: F821
    """ Steel Stencils for Alignment Jig
        Creates the gerber files needed to create steel stencils.
        These stencils are designed to be used with an acrilic alignment jig and a 3D
        printable support, that is also generated.
        [KiKit docs](https://github.com/yaqwsx/KiKit/blob/master/doc/stencil.md).
        Note that we don't implement `--ignore` option, you should use a variant for this """
    def __init__(self):
        super().__init__()
        with document:
            self.options = Stencil_For_Jig_Options
            """ *[dict] Options for the `stencil_for_jig` output """
