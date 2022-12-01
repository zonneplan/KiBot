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
import os
import shutil
import tempfile
from .error import PlotError
from .gs import GS
from .kiplot import run_command
from .out_base import VariantOptions
from .misc import W_AUTONONE
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class Stencil_3D_Options(VariantOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i='stencil_3d_top'|'stencil_3d_bottom'|'stencil_3d_edge',
                 %x='stl'|'scad'|'dxf') """
            self.side = 'auto'
            """ [top,bottom,auto,both] Which side of the PCB we want. Using `auto` will detect which
                side contains solder paste """
            self.include_scad = True
            """ Include the generated OpenSCAD files. Note that this also includes the DXF files """
            self.cutout = ''
            """ [string|list(string)] List of components to add a cutout based on the component courtyard.
                This is useful when you have already pre-populated board and you want to populate more
                components """
            self.pcbthickness = 0
            """ PCB thickness [mm]. If 0 we will ask KiCad """
            self.pcb_thickness = None
            """ {pcbthickness} """
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

    def config(self, parent):
        super().config(parent)
        self.cutout = ','.join(self.force_list(self.cutout))

    def move_output(self, src_dir, src_file, id, ext, replacement=None, patch=False):
        self._expand_id = id
        self._expand_ext = ext
        dst_name = self._parent.expand_filename(self._parent.output_dir, self.output)
        src_name = os.path.join(src_dir, src_file)
        if not os.path.isfile(src_name):
            raise PlotError('Missing output file {}'.format(src_name))
        if patch:
            # Adjust the names of the DXF files
            with open(src_name, 'r') as f:
                content = f.read()
            for k, v in replacement.items():
                content = content.replace(k, v)
            with open(dst_name, 'w') as f:
                f.write(content)
        else:
            shutil.move(src_name, dst_name)
            if replacement is not None:
                replacement[src_name] = os.path.basename(dst_name)

    def get_targets(self, out_dir):
        # TODO: auto side is tricky, needs variants applied
        return [self._parent.expand_filename(out_dir, self.output)]

    def run(self, output):
        cmd_kikit = self.ensure_tool('KiKit')
        self.ensure_tool('OpenSCAD')
        super().run(output)
        # Apply variants and filters
        filtered = self.filter_pcb_components(GS.board)
        if self.side == 'auto':
            detected_top, detected_bottom = self.detect_solder_paste(GS.board)
        fname = self.save_tmp_board() if filtered else GS.pcb_file
        if filtered:
            self.unfilter_pcb_components(GS.board)
        # Avoid running the tool if we will generate useless models
        if self.side == 'auto' and not detected_top and not detected_bottom:
            logger.warning(W_AUTONONE+'No solder paste detected, skipping 3D stencil generation')
            return
        # If no PCB thickness indicated ask KiCad
        if not self.pcbthickness:
            ds = GS.board.GetDesignSettings()
            self.pcbthickness = self.to_mm(ds.GetBoardThickness())
        # Create the command line
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
        with tempfile.TemporaryDirectory() as tmp:
            cmd.append(fname)
            cmd.append(tmp)
            try:
                run_command(cmd)
            finally:
                # Remove temporal variant
                if filtered:
                    GS.remove_pcb_and_pro(fname)
            # Now copy the files we want
            # - Which side?
            do_top = do_bottom = False
            if self.side == 'top':
                do_top = True
            elif self.side == 'bottom':
                do_bottom = True
            elif self.side == 'both':
                do_top = True
                do_bottom = True
            else:  # auto
                do_top = detected_top
                do_bottom = detected_bottom
            prj_name = os.path.splitext(os.path.basename(fname))[0]
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
            """ *[dict] Options for the `Stencil_3D` output """
