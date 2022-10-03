# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Description: Applies changes to fields
import re
from .optionable import Optionable
from .error import KiPlotConfigurationError
from .fil_base import BaseFilter
from .macros import macros, document, filter_class  # noqa: F401
from . import log


logger = log.get_logger()


@filter_class
class Field_Modify(BaseFilter):  # noqa: F821
    """ Field_Modify
        Changes the content of one or more fields """
    def __init__(self):
        super().__init__()
        self._is_transform = True
        with document:
            self.fields = Optionable
            """ [string|list(string)='Datasheet'] Fields to convert """
            self.regex = r'(https?://\S+)'
            """ Regular expression to match the field content.
                Only fields that matches will be modified.
                An empty regex will match anything.
                The example matches an HTTP URL """
            self.replace = r'<a href="\1">\1</a>'
            """ Text to replace, can contain references to sub-expressions.
                The example converts an HTTP URL into an HTML link, like the URLify filter """
            self.include = Optionable
            """ [string|list(string)=''] Name of the filter to select which components will be affected.
                Applied to all if nothing specified here """
        self._fields_example = 'Datasheet'
        self._include_solved = False

    def config(self, parent):
        super().config(parent)
        if isinstance(self.fields, type):
            self.fields = ['Datasheet']
        self.fields = Optionable.force_list(self.fields)
        try:
            self._regex = re.compile(self.regex)
        except Exception as e:
            raise KiPlotConfigurationError('Invalid regular expression '+str(e))

    def filter(self, comp):
        """ Apply the regex substitution """
        if not self._include_solved:
            self.include = BaseFilter.solve_filter(self.include, 'include')
            self._include_solved = True
        if self.include and not self.include.filter(comp):
            return
        for fld in self.fields:
            value = comp.get_field_value(fld)
            if not value:
                continue
            new_value = self._regex.sub(self.replace, value)
            if new_value != value:
                logger.debugl(2, '{}: {} -> {}'.format(fld, value, new_value))
                comp.set_field(fld, new_value)
