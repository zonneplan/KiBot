# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from .optionable import Optionable


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


class RegOutput(Optionable, Registrable):
    """ An optionable that is also registrable.
        Used by BaseOutput.
        Here because it doesn't need macros. """
    _registered = {}
    # List of defined variants
    _def_variants = {}

    def __init__(self):
        super().__init__()

    @staticmethod
    def set_variants(variants):
        RegOutput._def_variants = variants


class RegVariant(Optionable, Registrable):
    """ An optionable that is also registrable.
        Used by BaseVariant.
        Here because it doesn't need macros. """
    _registered = {}

    def __init__(self):
        super().__init__()
