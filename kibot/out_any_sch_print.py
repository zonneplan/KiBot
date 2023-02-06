# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from tempfile import mkdtemp
from shutil import copy2
from .gs import GS
from .out_base import VariantOptions
from .kicad.config import KiConf
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


def copy_project(sch_dir):
    """ Copy the project file to the temporal dir """
    ext = GS.pro_ext
    source = GS.pro_file
    prj_file = os.path.join(sch_dir, GS.sch_basename+ext)
    if source is not None and os.path.isfile(source):
        copy2(source, prj_file)
        KiConf.fix_page_layout(prj_file)
    else:
        # Create a dummy project file to avoid warnings
        f = open(prj_file, 'wt')
        f.close()


class Any_SCH_PrintOptions(VariantOptions):
    def __init__(self):
        with document:
            self.monochrome = False
            """ Generate a monochromatic output """
            self.frame = True
            """ *Include the frame and title block """
            self.all_pages = True
            """ Generate with all hierarchical sheets """
            self.color_theme = ''
            """ Color theme used, this must exist in the KiCad config (KiCad 6) """
            self.background_color = False
            """ Use the background color from the `color_theme` (KiCad 6) """
        super().__init__()
        self.add_to_doc('variant', "Not fitted components are crossed")
        self._expand_id = 'schematic'

    def get_targets(self, out_dir):
        if self.output:
            return [self._parent.expand_filename(out_dir, self.output)]
        return [self._parent.expand_filename(out_dir, '%f.%x')]

    def run(self, name):
        super().run(name)
        command = self.ensure_tool('KiAuto')
        if self._comps:
            # Save it to a temporal dir
            sch_dir = mkdtemp(prefix='tmp-kibot-'+self._expand_ext+'_sch_print-')
            copy_project(sch_dir)
            fname = GS.sch.save_variant(sch_dir)
            sch_file = os.path.join(sch_dir, fname)
            self._files_to_remove.append(sch_dir)
        else:
            sch_file = GS.sch_file
        fmt = 'hpgl' if self._expand_ext == 'plt' else self._expand_ext
        cmd = [command, 'export', '--file_format', fmt, '-o', name]
        if self.monochrome:
            cmd.append('--monochrome')
        if not self.frame:
            cmd.append('--no_frame')
        if self.all_pages:
            cmd.append('--all_pages')
        if self.color_theme:
            cmd.extend(['--color_theme', self.color_theme])
        if self.background_color:
            cmd.append('--background_color')
        if hasattr(self, '_origin'):
            cmd.extend(['--hpgl_origin', str(self._origin)])
        if hasattr(self, 'pen_size'):
            cmd.extend(['--hpgl_pen_size', str(self.pen_size)])
        cmd.extend([sch_file, os.path.dirname(name)])
        self.exec_with_retry(self.add_extra_options(cmd), self._exit_error)
