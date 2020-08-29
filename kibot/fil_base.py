# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from .registrable import RegFilter
from .macros import macros, document  # noqa: F401


class BaseFilter(RegFilter):
    def __init__(self):
        super().__init__()
        self._unkown_is_error = True
        with document:
            self.name = ''
            """ Used to identify this particular filter definition """
            self.type = ''
            """ Type of filter """
            self.comment = ''
            """ A comment for documentation purposes """
