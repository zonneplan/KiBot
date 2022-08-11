# -*- coding: utf-8 -*-
# Copyright (c) 2020-2022 Salvador E. Tropea
# Copyright (c) 2020-2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from tempfile import mkdtemp
from shutil import rmtree, copy2
from .gs import GS
from .kiplot import add_extra_options, exec_with_retry
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
            """ Generate a monochromatic PDF """
            self.frame = True
            """ *Include the frame and title block """
            self.all_pages = True
            """ Generate with all hierarchical sheets """
        super().__init__()
        self.add_to_doc('variant', "Not fitted components are crossed")
        self._expand_id = 'schematic'

    def get_targets(self, out_dir):
        if self.output:
            return [self._parent.expand_filename(out_dir, self.output)]
        return [self._parent.expand_filename(out_dir, '%f.%x')]

    def run(self, name):
        super().run(name)
        output_dir = os.path.dirname(name)
        our_name = self._expand_ext+'_sch_print'
        command = self.ensure_tool('KiAuto')
        if self._comps:
            # Save it to a temporal dir
            sch_dir = mkdtemp(prefix='tmp-kibot-'+our_name+'-')
            copy_project(sch_dir)
            fname = GS.sch.save_variant(sch_dir)
            sch_file = os.path.join(sch_dir, fname)
        else:
            sch_dir = None
            sch_file = GS.sch_file
        cmd = [command, 'export', '--file_format', self._expand_ext, '-o', name]
        if self.monochrome:
            cmd.append('--monochrome')
        if not self.frame:
            cmd.append('--no_frame')
        if self.all_pages:
            cmd.append('--all_pages')
        cmd.extend([sch_file, output_dir])
        cmd, video_remove = add_extra_options(cmd)
        ret = exec_with_retry(cmd)
        if ret:
            logger.error(command+' returned %d', ret)
            exit(self._exit_error)
        # Remove the temporal dir if needed
        if sch_dir:
            logger.debug('Removing temporal variant dir `{}`'.format(sch_dir))
            rmtree(sch_dir)
        if video_remove:
            video_name = os.path.join(output_dir, 'export_eeschema_screencast.ogv')
            if os.path.isfile(video_name):
                os.remove(video_name)
