# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Contributors: Leandro Heck (@leoheck)
import os
from .gs import GS
from .error import KiPlotConfigurationError
from .optionable import Optionable
from .macros import macros, document, pre_class  # noqa: F401
from .log import get_logger

logger = get_logger(__name__)


class FilterOptions(Optionable):
    """ Valid options for a filter entry """
    def __init__(self):
        super().__init__()
        self._unkown_is_error = True
        with document:
            self.filter = ''
            """ Name for the filter, for documentation purposes """
            self.filter_msg = None
            """ {filter} """
            self.number = 0
            """ Error number we want to exclude """
            self.error_number = None
            """ {number} """
            self.regex = 'None'
            """ Regular expression to match the text for the error we want to exclude """
            self.regexp = None
            """ {regex} """


class FiltersOptions(Optionable):
    """ A list of filter entries """
    def __init__(self):
        super().__init__()
        with document:
            self.filters = FilterOptions
            """ [list(dict)] DRC/ERC errors to be ignored """

    def config(self):
        super().config()
        parsed = None
        for f in self.filters:
            where = ' (in `{}` filter)'.format(f.filter) if f.filter else ''
            number = f.number
            if not number:
                raise KiPlotConfigurationError('Missing `number`'+where)
            regex = f.regex
            if regex == 'None':
                raise KiPlotConfigurationError('Missing `regex`'+where)
            comment = f.filter
            logger.debug("Adding DRC/ERC filter '{}','{}','{}'".format(comment, number, regex))
            if parsed is None:
                parsed = ''
            if comment:
                parsed += '# '+comment+'\n'
            parsed += '{},{}\n'.format(number, regex)
        self.filters = parsed


@pre_class
class Filters(BasePreFlight):  # noqa: F821
    """ [list(dict)] A list of entries to filter out ERC/DRC messages """
    def __init__(self, name, value):
        f = FiltersOptions()
        f.set_tree({'filters': value})
        f.config()
        super().__init__(name, f.filters)

    def get_example():
        """ Returns a YAML value for the example config """
        return "\n    - filter: 'Filter description'\n      number: 10\n      regex: 'Regular expression to match'"

    @classmethod
    def get_doc(cls):
        return cls.__doc__, FilterOptions

    def apply(self):
        # Create the filters file
        if self._value:
            GS.filter_file = os.path.join(GS.out_dir, 'kibot_errors.filter')
            with open(GS.filter_file, 'w') as f:
                f.write(self._value)
