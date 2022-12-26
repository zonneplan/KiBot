# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - from: KiAuto
    role: mandatory
    version: 1.6.5
"""
import os
from .gs import GS
from .out_base import VariantOptions
from .misc import FAILED_EXECUTE
from .kiplot import exec_with_retry, add_extra_options
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class GenCADOptions(VariantOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i=gencad, %x=cad) """
            self.flip_bottom_padstacks = False
            """ Flip bottom footprint padstacks """
            self.unique_pin_names = False
            """ Generate unique pin names """
            self.no_reuse_shapes = False
            """ Generate a new shape for each footprint instance (Do not reuse shapes) """
            self.aux_origin = False
            """ Use auxiliary axis as origin """
            self.save_origin = False
            """ Save the origin coordinates in the file """
        super().__init__()
        self._expand_id = 'gencad'
        self._expand_ext = 'cad'
        self.help_only_sub_pcbs()

    def get_targets(self, out_dir):
        return [self._parent.expand_filename(out_dir, self.output)]

    def run(self, name):
        command = self.ensure_tool('KiAuto')
        super().run(name)
        to_remove = []
        board_name = self.save_tmp_board_if_variant(to_remove)
        # Output file name
        cmd = [command, 'export_gencad', '--output_name', os.path.basename(name)]
        if self.flip_bottom_padstacks:
            cmd.append('--flip_bottom_padstacks')
        if self.unique_pin_names:
            cmd.append('--unique_pin_names')
        if self.no_reuse_shapes:
            cmd.append('--no_reuse_shapes')
        if self.aux_origin:
            cmd.append('--aux_origin')
        if self.save_origin:
            cmd.append('--save_origin')
        cmd.extend([board_name, os.path.dirname(name)])
        cmd, video_remove = add_extra_options(cmd)
        if video_remove:
            to_remove.append(os.path.join(self.expand_filename_pcb(GS.out_dir), 'pcbnew_export_gencad_screencast.ogv'))
        # Execute it
        ret = exec_with_retry(cmd)
        if ret:
            logger.error(command+' returned %d', ret)
            exit(FAILED_EXECUTE)
        for f in to_remove:
            if os.path.isfile(f):
                os.remove(f)


@output_class
class GenCAD(BaseOutput):  # noqa: F821
    """ GenCAD
        Exports the PCB in GENCAD format.
        This format is interpreted by some CADCAM software and helps certain
        manufacturers """
    def __init__(self):
        super().__init__()
        self._category = 'PCB/export'
        with document:
            self.options = GenCADOptions
            """ *[dict] Options for the `gencad` output """

    @staticmethod
    def get_conf_examples(name, layers, templates):
        return BaseOutput.simple_conf_examples(name, 'PCB in GenCAD format', 'Export')  # noqa: F821
