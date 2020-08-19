# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from .reg_out import RegOutput
from .macros import macros, document  # noqa: F401
from . import log

logger = log.get_logger(__name__)


class BaseOutput(RegOutput):
    _registered = {}

    def __init__(self):
        super().__init__()
        with document:
            self.name = ''
            """ Used to identify this particular output definition """
            self.type = ''
            """ Type of output """
            self.dir = '.'
            """ Output directory for the generated files """
            self.comment = ''
            """ A comment for documentation purposes """  # pragma: no cover
        self._sch_related = False
        self._unkown_is_error = True

    @staticmethod
    def attr2longopt(attr):
        return '--'+attr.replace('_', '-')

    def __str__(self):
        return "'{}' ({}) [{}]".format(self.comment, self.name, self.type)

    def is_sch(self):
        """ True for outputs that works on the schematic """
        return self._sch_related

    def is_pcb(self):
        """ True for outputs that works on the PCB """
        return not self._sch_related

    def config(self):
        super().config()
        if getattr(self, 'options', None) and isinstance(self.options, type):
            # No options, get the defaults
            self.options = self.options()
            # Configure them using an empty tree
            self.options.config()

    def run(self, output_dir, board):
        self.options.run(output_dir, board)
