# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from .registrable import RegVariant
from .macros import macros, document  # noqa: F401


class BaseVariant(RegVariant):
    def __init__(self):
        super().__init__()
        with document:
            self.name = ''
            """ Used to identify this particular variant definition """
            self.type = ''
            """ Type of variant """
            self.comment = ''
            """ A comment for documentation purposes """
            self.file_id = ''
            """ Text to use as the """

    def __str__(self):
        return "'{}' ({}) [{}]".format(self.comment, self.name, self.type)
