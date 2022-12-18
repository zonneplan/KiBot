# -*- coding: utf-8 -*-
# Copyright (c) 2020-2022 Salvador E. Tropea
# Copyright (c) 2020-2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from .registrable import RegVariant
from .optionable import Optionable, PanelOptions
from .fil_base import apply_exclude_filter, apply_fitted_filter, apply_fixed_filter, apply_pre_transform
from .error import KiPlotConfigurationError
from .misc import KIKIT_UNIT_ALIASES
from .gs import GS
from .kiplot import load_board, run_command
from .macros import macros, document  # noqa: F401


class SubPCBOptions(PanelOptions):
    def __init__(self):
        super().__init__()
        self._unkown_is_error = True
        with document:
            self.name = ''
            """ *Name for this sub-pcb """
            self.reference = ''
            """ *Use it for the annotations method.
                This is the reference for the `kikit:Board` footprint used to identify the sub-PCB.
                When empty the sub-PCB is specified using a rectangle """
            self.ref = None
            """ {reference} """
            self.tlx = 0
            """ [number|string] The X position of the top left corner for the rectangle that contains the sub-PCB """
            self.top_left_x = None
            """ {tlx} """
            self.tly = 0
            """ [number|string] The Y position of the top left corner for the rectangle that contains the sub-PCB """
            self.top_left_y = None
            """ {tly} """
            self.brx = 0
            """ [number|string] The X position of the bottom right corner for the rectangle that contains the sub-PCB """
            self.bottom_right_x = None
            """ {brx} """
            self.bry = 0
            """ [number|string] The Y position of the bottom right corner for the rectangle that contains the sub-PCB """
            self.bottom_right_y = None
            """ {bry} """
            self.units = 'mm'
            """ [millimeters,inches,mils,mm,cm,dm,m,mil,inch,in] Units used when omitted """
            self.file_id = ''
            """ Text to use as the replacement for %v expansion.
                When empty we use the parent `file_id` plus the `name` of the sub-PCB """

    def is_zero(self, val):
        return isinstance(val, (int, float)) and val == 0

    def config(self, parent):
        super().config(parent)
        if not self.name:
            raise KiPlotConfigurationError('Sub-PCB without a name')
        self.units = KIKIT_UNIT_ALIASES.get(self.units, self.units)
        if (not self.reference and self.is_zero(self.tlx) and self.is_zero(self.tly) and self.is_zero(self.brx) and
           self.is_zero(self.bry)):
            raise KiPlotConfigurationError('No reference or rectangle specified for {} sub-PCB'.format(self.name))
        self.add_units(('tlx', 'tly', 'brx', 'bry'), self.units)

    def get_separate_source(self):
        if self.reference:
            return "annotation; ref: {}".format(self.reference)
        return "rectangle; tlx: {}; tly: {}; brx: {}; bry: {}".format(self.tlx, self.tly, self.brx, self.bry)

    def load_board(self, dest):
        # Make sure kikit is available
        command = GS.ensure_tool('global', 'KiKit')
        # Execute the separate
        cmd = [command, 'separate', '-s', self.get_separate_source(), GS.pcb_file, dest]
        run_command(cmd)
        # Load this board
        GS.board = None
        load_board(dest)


class BaseVariant(RegVariant):
    def __init__(self):
        super().__init__()
        self._unkown_is_error = True
        with document:
            self.name = ''
            """ Used to identify this particular variant definition """
            self.type = ''
            """ Type of variant """
            self.comment = ''
            """ A comment for documentation purposes """
            self.file_id = ''
            """ Text to use as the replacement for %v expansion """
            # * Filters
            self.pre_transform = Optionable
            """ [string|list(string)=''] Name of the filter to transform fields before applying other filters.
                Use '_var_rename' to transform VARIANT:FIELD fields.
                Use '_var_rename_kicost' to transform kicost.VARIANT:FIELD fields.
                Use '_kicost_rename' to apply KiCost field rename rules """
            self.exclude_filter = Optionable
            """ [string|list(string)=''] Name of the filter to exclude components from BoM processing.
                Use '_mechanical' for the default KiBoM behavior """
            self.dnf_filter = Optionable
            """ [string|list(string)=''] Name of the filter to mark components as 'Do Not Fit'.
                Use '_kibom_dnf' for the default KiBoM behavior.
                Use '_kicost_dnp'' for the default KiCost behavior """
            self.dnc_filter = Optionable
            """ [string|list(string)=''] Name of the filter to mark components as 'Do Not Change'.
                Use '_kibom_dnc' for the default KiBoM behavior """
            self.sub_pcbs = SubPCBOptions
            """ [list(dict)] Used for multi-board workflows as defined by KiKit.
                I don't recommend using it, for detail read
                [this](https://github.com/INTI-CMNB/KiBot/tree/master/docs/1_SCH_2_part_PCBs).
                But if you really need it you can define the sub-PCBs here.
                Then you just use *VARIANT[SUB_PCB_NAME]* instead of just *VARIANT* """
        self._sub_pcb = None

    def config(self, parent):
        super().config(parent)
        if isinstance(self.sub_pcbs, type):
            self.sub_pcbs = []

    def get_variant_field(self):
        """ Returns the name of the field used to determine if the component belongs to the variant """
        return None

    def matches_variant(self, text):
        """ This is a generic match mechanism used by variants that doesn't really have a matching mechanism """
        return self.name.lower() == text.lower()

    def filter(self, comps):
        # Apply all the filters
        comps = apply_pre_transform(comps, self.pre_transform)
        apply_exclude_filter(comps, self.exclude_filter)
        apply_fitted_filter(comps, self.dnf_filter)
        apply_fixed_filter(comps, self.dnc_filter)
        return comps
