# -*- coding: utf-8 -*-
# Copyright (c) 2020-2022 Salvador E. Tropea
# Copyright (c) 2020-2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from .gs import GS
from .macros import macros, document  # noqa: F401
from .pre_filters import FiltersOptions
from .log import get_logger, set_filters
from .misc import W_MUSTBEINT


class Globals(FiltersOptions):
    """ Global options """
    def __init__(self):
        super().__init__()
        with document:
            self.output = ''
            """ Default pattern for output file names """
            self.dir = ''
            """ Default pattern for the output directories """
            self.out_dir = ''
            """ Base output dir, same as command line `--out-dir` """
            self.variant = ''
            """ Default variant to apply to all outputs """
            self.kiauto_wait_start = 0
            """ Time to wait for KiCad in KiAuto operations """
            self.kiauto_time_out_scale = 0.0
            """ Time-out multiplier for KiAuto operations """
            self.date_time_format = '%Y-%m-%d_%H-%M-%S'
            """ Format used for the PCB and schematic date when using the file timestamp. Uses the `strftime` format """
            self.date_format = '%Y-%m-%d'
            """ Format used for the day we started the script.
                Is also used for the PCB/SCH date formatting when `time_reformat` is enabled (default behavior).
                Uses the `strftime` format """
            self.time_format = '%H-%M-%S'
            """ Format used for the time we started the script. Uses the `strftime` format """
            self.time_reformat = True
            """ Tries to reformat the PCB/SCH date using the `date_format`.
                This assumes you let KiCad fill this value and hence the time is in ISO format (YY-MM-DD) """
            self.pcb_material = 'FR4'
            """ PCB core material. Currently used for documentation and to choose default colors.
                Currently known are FR1 to FR5 """
            self.solder_mask_color = 'green'
            """ Color for the solder mask. Currently used for documentation and to choose default colors.
                Currently known are green, black, white, yellow, purple, blue and red """
            self.silk_screen_color = 'white'
            """ Color for the markings. Currently used for documentation and to choose default colors.
                Currently known are black and white """
            self.pcb_finish = 'HAL'
            """ Finishing used to protect pads. Currently used for documentation and to choose default colors.
                Currently known are None, HAL, HASL, ENIG and ImAg """
        self.set_doc('filters', " [list(dict)] KiBot warnings to be ignored ")
        self._filter_what = 'KiBot warnings'
        self._unkown_is_error = True
        self._error_context = 'global '

    @staticmethod
    def set_global(current, new_val, opt):
        if current is not None:
            logger.info('Using command line value `{}` for global option `{}`'.format(current, opt))
            return current
        if new_val:
            return new_val
        return current

    def config(self, parent):
        super().config(parent)
        GS.global_output = self.set_global(GS.global_output, self.output, 'output')
        GS.global_dir = self.set_global(GS.global_dir, self.dir, 'dir')
        GS.global_variant = self.set_global(GS.global_variant, self.variant, 'variant')
        GS.global_date_time_format = self.set_global(GS.global_date_time_format, self.date_time_format, 'date_time_format')
        GS.global_date_format = self.set_global(GS.global_date_format, self.date_format, 'date_format')
        GS.global_time_format = self.set_global(GS.global_time_format, self.time_format, 'time_format')
        GS.global_time_reformat = self.set_global(GS.global_time_reformat, self.time_reformat, 'time_reformat')
        GS.global_kiauto_wait_start = self.set_global(GS.global_kiauto_wait_start, self.kiauto_wait_start, 'kiauto_wait_start')
        if GS.global_kiauto_wait_start and int(GS.global_kiauto_wait_start) != GS.global_kiauto_wait_start:
            GS.global_kiauto_wait_start = int(GS.global_kiauto_wait_start)
            logger.warning(W_MUSTBEINT+'kiauto_wait_start must be integer, truncating to '+str(GS.global_kiauto_wait_start))
        GS.global_kiauto_time_out_scale = self.set_global(GS.global_kiauto_time_out_scale, self.kiauto_time_out_scale,
                                                          'kiauto_time_out_scale')
        GS.global_pcb_material = self.set_global(GS.global_pcb_material, self.pcb_material, 'pcb_material')
        GS.global_solder_mask_color = self.set_global(GS.global_solder_mask_color, self.solder_mask_color,
                                                      'solder_mask_color')
        GS.global_silk_screen_color = self.set_global(GS.global_silk_screen_color, self.silk_screen_color,
                                                      'silk_screen_color')
        GS.global_pcb_finish = self.set_global(GS.global_pcb_finish, self.pcb_finish, 'pcb_finish')
        if not GS.out_dir_in_cmd_line and self.out_dir:
            GS.out_dir = os.path.join(os.getcwd(), self.out_dir)
        set_filters(self.unparsed)


logger = get_logger(__name__)
GS.global_opts_class = Globals
