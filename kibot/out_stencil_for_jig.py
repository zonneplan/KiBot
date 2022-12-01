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


class Stencil_For_Jig_Options(VariantOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i='stencil_for_jig_top'|'stencil_for_jig_bottom',
                 %x='stl'|'scad'|'gbp'|'gtp'|'gbrjob') """
            self.side = 'auto'
            """ [top,bottom,auto,both] Which side of the PCB we want. Using `auto` will detect which
                side contains solder paste """
            self.include_scad = True
            """ Include the generated OpenSCAD files """
            self.cutout = ''
            """ [string|list(string)] List of components to add a cutout based on the component courtyard.
                This is useful when you have already pre-populated board and you want to populate more
                components """
            self.pcbthickness = 0
            """ PCB thickness [mm]. If 0 we will ask KiCad """
            self.pcb_thickness = None
            """ {pcbthickness} """
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

    def config(self, parent):
        super().config(parent)
        self.cutout = ','.join(self.force_list(self.cutout))

    def move_output(self, src_dir, src_file, id, ext, replacement=None, patch=False, relative=False):
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
                if relative:
                    src_name = os.path.basename(src_name)
                replacement[src_name] = os.path.basename(dst_name)

    def get_targets(self, out_dir):
        # TODO: auto side is tricky, needs variants applied
        return [self._parent.expand_filename(out_dir, self.output)]

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
            logger.warning(W_AUTONONE+'No solder paste detected, skipping stencil generation')
            return
        # If no PCB thickness indicated ask KiCad
        if not self.pcbthickness:
            ds = GS.board.GetDesignSettings()
            self.pcbthickness = self.to_mm(ds.GetBoardThickness())
        # Create the command line
        cmd = self.create_cmd(cmd_kikit)
        # Create the outputs
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
            self.move_outputs(tmp, prj_name, do_top, do_bottom)


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
