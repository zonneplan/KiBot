# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from .registrable import RegVariant
from .optionable import Optionable
from .fil_base import BaseFilter
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

    def config(self):
        super().config()
        # exclude_filter
        self.exclude_filter = BaseFilter.solve_filter(self.exclude_filter, 'exclude_filter')
        # dnf_filter
        self.dnf_filter = BaseFilter.solve_filter(self.dnf_filter, 'dnf_filter')
        # dnc_filter
        self.dnc_filter = BaseFilter.solve_filter(self.dnc_filter, 'dnc_filter')

    def filter(self, comps):
        # Apply all the filters
        if self.exclude_filter:
            for c in comps:
                c.in_bom = self.exclude_filter.filter(c)
        if self.dnf_filter:
            for c in comps:
                c.fitted = self.dnf_filter.filter(c)
        if self.dnc_filter:
            for c in comps:
                c.fixed = self.dnc_filter.filter(c)
