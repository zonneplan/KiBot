# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from .registrable import RegFilter, Registrable, RegOutput
from .error import KiPlotConfigurationError
from .macros import macros, document  # noqa: F401


class DummyFilter(Registrable):
    """ A filter that allows all """
    def __init__(self):
        super().__init__()
        self.name = 'Dummy'
        self.type = 'dummy'
        self.comment = 'A filter that does nothing'

    def filter(self, comp):
        return True


class MultiFilter(Registrable):
    """ A filter containing a list of filters.
        They are applied in sequence. """
    def __init__(self, filters):
        super().__init__()
        self.name = ','.join([f.name for f in filters])
        self.type = ','.join([f.type for f in filters])
        self.comment = 'Multi-filter'
        self.filters = filters

    def filter(self, comp):
        for f in self.filters:
            if not f.filter(comp):
                return False
        return True


class NotFilter(Registrable):
    """ A filter that returns the inverted result """
    def __init__(self, filter):
        super().__init__()
        self.name = filter.name
        self.type = '!'+filter.type
        self.comment = filter.comment
        self.filter = filter

    def filter(self, comp):
        return not self.filter(comp)


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

    @staticmethod
    def solve_filter(name, def_key, def_real, creator, target_name):
        """ Name can be:
            - A class, meaning we have to use a default.
            - A string, the name of a filter.
            - A list of strings, the name of 1 or more filters.
            If any of the names matches def_key we call creator asking to create the filter.
            If def_real is not None we pass this name to creator. """
        if isinstance(name, type):
            # Nothing specified, use the default
            names = [def_key]
        elif isinstance(name, str):
            # User provided, but only one, make a list
            names = [name]
        # Here we should have a list of strings
        filters = []
        for name in names:
            if name[0] == '!':
                invert = True
                name = name[1:]
            else:
                invert = False
            filter = None
            if name == def_key:
                # Matched the default name, translate it to the real name
                if def_real:
                    name = def_real
                # Is already defined?
                if RegOutput.is_filter(name):
                    filter = RegOutput.get_filter(name)
                else:  # Nope, create it
                    tree = creator(name)
                    filter = RegFilter.get_class_for(tree['type'])()
                    filter.set_tree(tree)
                    filter.config()
                    RegOutput.add_filter(filter)
            elif name:
                # A filter that is supposed to exist
                if not RegOutput.is_filter(name):
                    raise KiPlotConfigurationError("Unknown filter `{}` used for `{}`".format(name, target_name))
                filter = RegOutput.get_filter(name)
            if filter:
                if invert:
                    filters.append(NotFilter(filter))
                else:
                    filters.append(filter)
        # Finished collecting filters
        if not filters:
            return DummyFilter()
        if len(filters) == 1:
            return filters[0]
        return MultiFilter(filters)
