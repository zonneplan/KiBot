# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from .optionable import Optionable


class RegOutput(Optionable):
    """ This class adds the mechanism to register outputs """
    _registered = {}

    def __init__(self):
        super().__init__()

    @staticmethod
    def register(name, aclass):
        RegOutput._registered[name] = aclass

    @staticmethod
    def is_registered(name):
        return name in RegOutput._registered

    @staticmethod
    def get_class_for(name):
        return RegOutput._registered[name]

    @staticmethod
    def get_registered():
        return RegOutput._registered
