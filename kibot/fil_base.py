# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from .registrable import RegFilter, Registrable, RegOutput
from .misc import IFILL_MECHANICAL
from .error import KiPlotConfigurationError
from .bom.columnlist import ColumnList
from .macros import macros, document  # noqa: F401
from . import log

logger = log.get_logger(__name__)
DEFAULT_EXCLUDE = [{'column': ColumnList.COL_REFERENCE, 'regex': '^TP[0-9]*'},
                   {'column': ColumnList.COL_REFERENCE, 'regex': '^FID'},
                   {'column': ColumnList.COL_PART, 'regex': 'mount.*hole'},
                   {'column': ColumnList.COL_PART, 'regex': 'solder.*bridge'},
                   {'column': ColumnList.COL_PART, 'regex': 'solder.*jump'},
                   {'column': ColumnList.COL_PART, 'regex': 'test.*point'},
                   {'column': ColumnList.COL_FP, 'regex': 'test.*point'},
                   {'column': ColumnList.COL_FP, 'regex': 'mount.*hole'},
                   {'column': ColumnList.COL_FP, 'regex': 'fiducial'},
                   ]


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
        self.name = 'Not '+filter.name
        self.type = '!'+filter.type
        self.comment = filter.comment
        self._filter = filter

    def filter(self, comp):
        return not self._filter.filter(comp)


def reset_filters(comps):
    for c in comps:
        c.included = True
        c.fitted = True
        c.fixed = False


def apply_exclude_filter(comps, filter):
    if filter:
        logger.debug('Applying filter `{}` to exclude'.format(filter.name))
        for c in comps:
            if c.included:
                c.included = filter.filter(c)


def apply_fitted_filter(comps, filter):
    if filter:
        logger.debug('Applying filter `{}` to fitted'.format(filter.name))
        for c in comps:
            if c.fitted:
                c.fitted = filter.filter(c)


def apply_fixed_filter(comps, filter):
    if filter:
        logger.debug('Applying filter `{}` to fixed'.format(filter.name))
        for c in comps:
            if not c.fixed:
                c.fixed = filter.filter(c)


class BaseFilter(RegFilter):
    def __init__(self):
        super().__init__()
        self._unkown_is_error = True
        self._internal = False
        with document:
            self.name = ''
            """ Used to identify this particular filter definition """
            self.type = ''
            """ Type of filter """
            self.comment = ''
            """ A comment for documentation purposes """

    def config(self):
        super().config()
        if self.name[0] == '_' and not self._internal:
            raise KiPlotConfigurationError('Filter names starting with `_` are reserved ({})'.format(self.name))

    @staticmethod
    def _create_mechanical(name):
        o_tree = {'name': name}
        o_tree['type'] = 'generic'
        o_tree['comment'] = 'Internal default mechanical filter'
        o_tree['exclude_all_hash_ref'] = True
        o_tree['exclude_any'] = DEFAULT_EXCLUDE
        o_tree['exclude_virtual'] = True
        logger.debug('Creating internal filter: '+str(o_tree))
        return o_tree

    @staticmethod
    def _create_kibom_dnx(name):
        type = name[7:10]
        if len(name) > 11:
            subtype = name[11:]
        else:
            subtype = 'config'
        o_tree = {'name': name}
        o_tree['type'] = 'generic'
        o_tree['comment'] = 'Internal KiBoM '+type.upper()+' filter ('+subtype+')'
        o_tree['config_field'] = subtype
        o_tree['exclude_value'] = True
        o_tree['exclude_config'] = True
        o_tree['keys'] = type+'_list'
        if type[-1] == 'c':
            o_tree['invert'] = True
        logger.debug('Creating internal filter: '+str(o_tree))
        return o_tree

    @staticmethod
    def _create_internal_filter(name):
        if name == IFILL_MECHANICAL:
            tree = BaseFilter._create_mechanical(name)
        elif name.startswith('_kibom_dn') and len(name) >= 10:
            tree = BaseFilter._create_kibom_dnx(name)
        else:
            return None
        filter = RegFilter.get_class_for(tree['type'])()
        filter._internal = True
        filter.set_tree(tree)
        filter.config()
        RegOutput.add_filter(filter)
        return filter

    @staticmethod
    def solve_filter(names, target_name, default=None):
        """ Name can be:
            - A class, meaning we have to use a default.
            - A string, the name of a filter.
            - A list of strings, the name of 1 or more filters.
            If any of the names matches def_key we call creator asking to create the filter.
            If def_real is not None we pass this name to creator. """
        if isinstance(names, type):
            # Nothing specified, use the default
            if default is None:
                return None
            names = [default]
        elif isinstance(names, str):
            # User provided, but only one, make a list
            if names == '_none':
                return None
            names = [names]
        # Here we should have a list of strings
        filters = []
        for name in names:
            if not name:
                continue
            if isinstance(name, Registrable):
                # A filter already converted
                filters.append(name)
                continue
            if name[0] == '!':
                invert = True
                name = name[1:]
                # '!' => always False
                if not name:
                    filters.append(NotFilter(DummyFilter()))
                    continue
            else:
                invert = False
            # Is already defined?
            if RegOutput.is_filter(name):
                filter = RegOutput.get_filter(name)
            else:  # Nope, can be created?
                filter = BaseFilter._create_internal_filter(name)
                if filter is None:
                    raise KiPlotConfigurationError("Unknown filter `{}` used for `{}`".format(name, target_name))
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
