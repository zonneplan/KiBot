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
from .misc import W_AUTONONE
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
