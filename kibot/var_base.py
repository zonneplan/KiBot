# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from .registrable import RegVariant
from .optionable import Optionable
from .fil_base import apply_exclude_filter, apply_fitted_filter, apply_fixed_filter
from .macros import macros, document  # noqa: F401


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
            """ Text to use as the """
            # * Filters
            self.exclude_filter = Optionable
            """ [string|list(string)=''] Name of the filter to exclude components from BoM processing.
                Use '_mechanical' for the default KiBoM behavior """
            self.dnf_filter = Optionable
            """ [string|list(string)=''] Name of the filter to mark components as 'Do Not Fit'.
                Use '_kibom_dnf' for the default KiBoM behavior """
            self.dnc_filter = Optionable
            """ [string|list(string)=''] Name of the filter to mark components as 'Do Not Change'.
                Use '_kibom_dnc' for the default KiBoM behavior """

    def filter(self, comps):
        # Apply all the filters
        apply_exclude_filter(comps, self.exclude_filter)
        apply_fitted_filter(comps, self.dnf_filter)
        apply_fixed_filter(comps, self.dnc_filter)
