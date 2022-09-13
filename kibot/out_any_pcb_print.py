# -*- coding: utf-8 -*-
# Copyright (c) 2020-2022 Salvador E. Tropea
# Copyright (c) 2020-2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from shutil import rmtree
from .pre_base import BasePreFlight
from .gs import GS
from .kiplot import exec_with_retry, add_extra_options
from .misc import PDF_PCB_PRINT
from .out_base import VariantOptions
from .macros import macros, document, output_class  # noqa: F401
from .drill_marks import add_drill_marks, DRILL_MARKS_MAP
from .layer import Layer
from . import log

logger = log.get_logger()


class Any_PCB_PrintOptions(VariantOptions):
    def __init__(self):
        with document:
            self.output_name = None
            """ {output} """
            self.scaling = 1.0
            """ *Scale factor (0 means autoscaling). You should disable `plot_sheet_reference` when using it """
            self.plot_sheet_reference = True
            """ *Include the title-block """
            self.monochrome = False
            """ Print in black and white """
            self.separated = False
            """ *Print layers in separated pages """
            self.mirror = False
            """ Print mirrored (X axis inverted). ONLY for KiCad 6 """
            self.hide_excluded = False
            """ Hide components in the Fab layer that are marked as excluded by a variant.
                Affected by global options """
            self.title = ''
            """ Text used to replace the sheet title. %VALUE expansions are allowed.
                If it starts with `+` the text is concatenated """
            self.force_edge_cuts = True
            """ Only useful for KiCad 6 when printing in one page, you can disable the edge here.
                KiCad 5 forces it by default, and you can't control it from config files.
                Same for KiCad 6 when printing to separated pages """
            self.color_theme = '_builtin_classic'
            """ Selects the color theme. Onlyu applies to KiCad 6.
                To use the KiCad 6 default colors select `_builtin_default`.
                Usually user colors are stored as `user`, but you can give it another name """
        add_drill_marks(self)
        super().__init__()

    def config(self, parent):
        super().config(parent)
        self.drill_marks = DRILL_MARKS_MAP[self.drill_marks]

    def filter_components(self, force_copy):
        if not self._comps and not force_copy:
            return GS.pcb_file, None
        self.filter_pcb_components(GS.board)
        # Save the PCB to a temporal dir
        fname, pcb_dir = self.save_tmp_dir_board('pdf_pcb_print')
        self.unfilter_pcb_components(GS.board)
        return fname, pcb_dir

    def get_targets(self, out_dir):
        return [self._parent.expand_filename(out_dir, self.output)]

    def run(self, output, svg=False):
        super().run(self._layers)
        command = self.ensure_tool('KiAuto')
        # Output file name
        cmd = [command, 'export', '--output_name', output]
        if BasePreFlight.get_option('check_zone_fills'):
            cmd.append('-f')
        cmd.extend(['--scaling', str(self.scaling), '--pads', str(self.drill_marks)])
        if not self.plot_sheet_reference:
            cmd.append('--no-title')
        if self.monochrome:
            cmd.append('--monochrome')
        if self.separated:
            cmd.append('--separate')
        if self.mirror:
            cmd.append('--mirror')
        if self.color_theme != '_builtin_classic' and self.color_theme:
            cmd.extend(['--color_theme', self.color_theme])
        if svg:
            cmd.append('--svg')
        self.set_title(self.title)
        board_name, board_dir = self.filter_components(self.title != '')
        cmd.extend([board_name, os.path.dirname(output)])
        cmd, video_remove = add_extra_options(cmd)
        # Add the layers
        cmd.extend([la.layer for la in self._layers])
        if GS.ki6 and self.force_edge_cuts and not self.separated:
            cmd.append('Edge.Cuts')
        # Execute it
        ret = exec_with_retry(cmd)
        self.restore_title()
        # Remove the temporal PCB
        if board_dir:
            logger.debug('Removing temporal variant dir `{}`'.format(board_dir))
            rmtree(board_dir)
        if ret:
            logger.error(command+' returned %d', ret)
            exit(PDF_PCB_PRINT)
        if video_remove:
            video_name = os.path.join(self.expand_filename_pcb(GS.out_dir), 'pcbnew_export_screencast.ogv')
            if os.path.isfile(video_name):
                os.remove(video_name)

    def set_layers(self, layers):
        layers = Layer.solve(layers)
        self._layers = layers
        self._expand_id = '+'.join([la.suffix for la in layers])
