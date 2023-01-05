# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from collections import OrderedDict
from copy import copy
from .gs import GS
from .optionable import Optionable
from .error import KiPlotConfigurationError
from . import log

logger = log.get_logger()


def fname(file):
    if file:
        return ", while importing from `{}`".format(file)
    return ""


class Registrable(object):
    """ This class adds the mechanism to register plug-ins """
    def __init__(self):
        super().__init__()

    @classmethod
    def register(cl, name, aclass):
        cl._registered[name] = aclass

    @classmethod
    def is_registered(cl, name):
        return name in cl._registered

    @classmethod
    def get_class_for(cl, name):
        return cl._registered[name]

    @classmethod
    def get_registered(cl):
        return cl._registered

    def __str__(self):
        return "'{}' ({}) [{}]".format(self.comment, self.name, self.type)


class RegOutput(Optionable, Registrable):
    """ An optionable that is also registrable.
        Used by BaseOutput.
        Here because it doesn't need macros. """
    _registered = {}
    # Defined filters
    _def_filters = {}
    # Defined variants
    _def_variants = {}
    # Defined groups
    _def_groups = {}
    # List of defined outputs
    _def_outputs = OrderedDict()

    def __init__(self):
        super().__init__()

    @staticmethod
    def reset():
        # Defined filters
        RegOutput._def_filters = {}
        # Defined variants
        RegOutput._def_variants = {}
        # Defined groups
        RegOutput._def_groups = {}
        # List of defined outputs
        RegOutput._def_outputs = OrderedDict()

    @staticmethod
    def add_variants(variants):
        for k, v in variants.items():
            # Do we have sub-PCBs
            if v.sub_pcbs:
                # Add a variant for each sub-PCB
                for sp in v.sub_pcbs:
                    name = k+'['+sp.name+']'
                    vn = copy(v)
                    vn._sub_pcb = sp
                    if sp.file_id:
                        vn.file_id = sp.file_id
                    else:
                        vn.file_id += '_'+sp.name
                    RegOutput._def_variants[name] = vn
            else:
                RegOutput._def_variants[k] = v

    @staticmethod
    def is_variant(name):
        return name in RegOutput._def_variants

    @staticmethod
    def get_variant(name):
        return RegOutput._def_variants[name]

    @staticmethod
    def add_filters(filters):
        RegOutput._def_filters.update(filters)

    @staticmethod
    def is_filter(name):
        return name in RegOutput._def_filters

    @staticmethod
    def get_filter(name):
        return RegOutput._def_filters[name]

    @staticmethod
    def add_filter(obj):
        RegOutput._def_filters[obj.name] = obj

    @staticmethod
    def add_output(obj, file=None):
        if obj.name in RegOutput._def_outputs:
            raise KiPlotConfigurationError("Output name `{}` already defined".format(obj.name)+fname(file))
        if obj.name in RegOutput._def_groups:
            raise KiPlotConfigurationError("Output name `{}` already defined as group".format(obj.name)+fname(file))
        RegOutput._def_outputs[obj.name] = obj

    @staticmethod
    def add_outputs(objs, file=None):
        for o in objs:
            RegOutput.add_output(o, file)

    @staticmethod
    def add_group(name, lst, file=None):
        if name in RegOutput._def_groups:
            raise KiPlotConfigurationError("Group name `{}` already defined".format(name)+fname(file))
        if name in RegOutput._def_outputs:
            raise KiPlotConfigurationError("Group name `{}` already defined as output".format(name)+fname(file))
        RegOutput._def_groups[name] = lst

    @staticmethod
    def add_groups(objs, file=None):
        logger.debug('Adding groups: '+str(objs))
        for n, lst in objs.items():
            RegOutput.add_group(n, lst, file)

    @staticmethod
    def get_outputs():
        return RegOutput._def_outputs.values()

    @staticmethod
    def get_output(name):
        return RegOutput._def_outputs.get(name, None)

    @staticmethod
    def is_output_or_group(name):
        return name in RegOutput._def_outputs or name in RegOutput._def_groups

    @staticmethod
    def check_variant(variant):
        if variant:
            if isinstance(variant, RegVariant):
                return variant
            if not RegOutput.is_variant(variant):
                raise KiPlotConfigurationError("Unknown variant name `{}`".format(variant))
            return RegOutput.get_variant(variant)
        return None

    @staticmethod
    def solve_groups(targets, where, level=0):
        """ Replaces any group by its members.
            Returns a new list.
            Assumes the outputs and groups are valid. """
        new_targets = []
        # Avoid infinite loops
        level += 1
        if level > 20:
            raise KiPlotConfigurationError("More than 20 levels of nested groups, possible loop")
        for t in targets:
            if t in RegOutput._def_outputs:
                new_targets.append(t)
            else:
                new_grp = RegOutput._def_groups.get(t, None)
                if new_grp is None:
                    raise KiPlotConfigurationError('Unknown output/group `{}` (in `{}`)'.format(t, where))
                # Recursive expand
                new_targets.extend(RegOutput.solve_groups(new_grp, t, level))
        return new_targets


class RegVariant(Optionable, Registrable):
    """ An optionable that is also registrable.
        Used by BaseVariant.
        Here because it doesn't need macros. """
    _registered = {}

    def __init__(self):
        super().__init__()


class RegFilter(Optionable, Registrable):
    """ An optionable that is also registrable.
        Used by BaseFilter.
        Here because it doesn't need macros. """
    _registered = {}

    def __init__(self):
        super().__init__()


class RegDependency(Registrable):
    """ Used to register output tools dependencies """
    _registered = {}

    def __init__(self):
        super().__init__()

    @classmethod
    def register(cl, aclass):
        name = aclass.name
        if name in cl._registered:
            # Already registered, add the roles
            old_reg = cl._registered[name]
            old_reg.roles.extend(aclass.roles)
        else:
            cl._registered[name] = aclass


def solve_variant(variant):
    if isinstance(variant, str):
        return RegOutput.check_variant(variant)
    return variant


GS.solve_variant = solve_variant
