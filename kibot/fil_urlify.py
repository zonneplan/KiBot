# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Description: Converts URL style text into HTML links
import re
from .optionable import Optionable
from .macros import macros, document, filter_class  # noqa: F401
from . import log


logger = log.get_logger()
regex = re.compile(r'(https?://\S+)')


@filter_class
class URLify(BaseFilter):  # noqa: F821
    """ URLify
        Converts URL text in fields to HTML URLs """
    def __init__(self):
        super().__init__()
        self._is_transform = True
        with document:
            self.fields = Optionable
            """ [string|list(string)='Datasheet'] Fields to convert """
        self._fields_example = 'Datasheet'

    def config(self, parent):
        super().config(parent)
        if isinstance(self.fields, type):
            self.fields = ['Datasheet']
        self.fields = Optionable.force_list(self.fields)

    def filter(self, comp):
        """ Look for URLs and convert them """
        for fld in self.fields:
            value = comp.get_field_value(fld)
            if not value:
                continue
            new_value = regex.sub(r'<a href="\1">\1</a>', value)
            if new_value != value:
                logger.debugl(2, '{}: {} -> {}'.format(fld, value, new_value))
                comp.set_field(fld, new_value)
