# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
import shutil
import tempfile
from .error import PlotError
from .gs import GS
from .kiplot import run_command
from .out_base import VariantOptions
from .misc import W_AUTONONE, W_AUTOPROB
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class Stencil_Options(VariantOptions):
    def __init__(self):
        with document:
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
            self.create_preview = True
            """ Creates a PNG showing the generated 3D model """
        super().__init__()
        self._output_multiple_files = True

    def config(self, parent):
        super().config(parent)
        self.cutout = ','.join(self.force_list(self.cutout))

    def expand_name(self, id, ext, out_dir):
        self._expand_id = id
        self._expand_ext = ext
        return self._parent.expand_filename(out_dir, self.output)

    def create_preview_png(self, src_dir, src_file, id):
        dst_name = self.expand_name(id, 'png', self._parent.output_dir)
        src_name = os.path.join(src_dir, src_file)
        if not os.path.isfile(src_name):
            raise PlotError('Missing output file {}'.format(src_name))
        run_command([self.cmd_openscad, '-o', dst_name, '--imgsize=1280,720', src_name], use_x11=True)

    def move_output(self, src_dir, src_file, id, ext, replacement=None, patch=False, relative=False):
        dst_name = self.expand_name(id, ext, self._parent.output_dir)
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

    def find_sides(self, detected_top, detected_bottom, warn=False):
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
            if warn:
                logger.warning(W_AUTOPROB+'Using the `stencil.side: auto` option could create a wrong list of files.')
        return do_top, do_bottom

    def solve_sides(self):
        if self.side == 'auto':
            detected_top, detected_bottom = self.detect_solder_paste(GS.board)
        else:
            detected_top = detected_bottom = False
        return self.find_sides(detected_top, detected_bottom, warn=True)

    def run(self, output):
        cmd_kikit = self.ensure_tool('KiKit')
        self.cmd_openscad = self.ensure_tool('OpenSCAD')
        if not GS.on_windows:
            self.ensure_tool('Xvfbwrapper')
            self.ensure_tool('Xvfb')
        super().run(output)
        # Apply variants and filters
        filtered = self.filter_pcb_components()
        if self.side == 'auto':
            detected_top, detected_bottom = self.detect_solder_paste(GS.board)
        else:
            detected_top = detected_bottom = False
        fname = self.save_tmp_board() if filtered else GS.pcb_file
        if filtered:
            self.unfilter_pcb_components()
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
                run_command(cmd, use_x11=True)
            finally:
                # Remove temporal variant
                if filtered:
                    GS.remove_pcb_and_pro(fname)
            # Now copy the files we want
            do_top, do_bottom = self.find_sides(detected_top, detected_bottom)
            prj_name = os.path.splitext(os.path.basename(fname))[0]
            self.move_outputs(tmp, prj_name, do_top, do_bottom)
