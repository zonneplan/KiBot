# -*- coding: utf-8 -*-
# Copyright (c) 2021 Salvador E. Tropea
# Copyright (c) 2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Implements a field renamer
"""
from .optionable import Optionable
from .error import KiPlotConfigurationError
from .gs import GS
from .misc import W_EMPTYREN
from .macros import macros, document, filter_class  # noqa: F401
from . import log

logger = log.get_logger(__name__)


class FieldRename(Optionable):
    """ Field translation """
    def __init__(self):
        super().__init__()
        self._unkown_is_error = True
        with document:
            self.field = ''
            """ Name of the field to rename """
            self.name = ''
            """ New name """
        self._field_example = 'mpn'
        self._name_example = 'manf#'

    def config(self, parent):
        super().config(parent)
        if not self.field:
            raise KiPlotConfigurationError("Missing or empty `field` in rename list ({})".format(str(self._tree)))
        if not self.name:
            raise KiPlotConfigurationError("Missing or empty `name` in rename list ({})".format(str(self._tree)))
        self.field = self.field.lower()


@filter_class
class Field_Rename(BaseFilter):  # noqa: F821
    """ Field_Rename
        This filter implements a field renamer.
        The internal `_kicost_rename` filter emulates the KiCost behavior """
    def __init__(self):
        super().__init__()
        self._is_transform = True
        with document:
            self.rename = FieldRename
            """ [list(dict)] Fields to rename """

    def config(self, parent):
        super().config(parent)
        if isinstance(self.rename, type):
            self.rename = []
        if not self.rename:
            logger.warning(W_EMPTYREN+'Nothing to rename in filter `{}`'.format(self.name))
        self.rename = {f.field: f.name for f in self.rename}

    def filter(self, comp):
        """ Change the names of the specified fields """
        for f in set(comp.get_field_names()).intersection(self.rename):
            new_name = self.rename[f]
            if GS.debug_level > 2:
                logger.debug('ref: {} field: {} -> {}'.format(comp.ref, f, new_name))
            comp.rename_field(f, new_name)
