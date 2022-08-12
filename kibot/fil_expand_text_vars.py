# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Description: Expands KiCad 6 text variables
import os
from .gs import GS
from .kicad.config import KiConf, expand_env
from .macros import macros, document, filter_class  # noqa: F401
from . import log

logger = log.get_logger()


@filter_class
class Expand_Text_Vars(BaseFilter):  # noqa: F821
    """ Expand_Text_Vars
        This filter expands KiCad 6 text variables (${VARIABLE}) """
    def __init__(self):
        super().__init__()
        with document:
            self.include_os_env = False
            """ Also expand system environment variables """
            self.include_kicad_env = True
            """ Also expand KiCad environment variables """
        self._first_pass = True
        self._is_transform = True

    def filter(self, comp):
        if self._first_pass:
            # Ensure we initialized the KiCad environment variables
            KiConf.init(GS.sch_file)
            # Collect the "extra" variables
            self.extra_env = {}
            if self.include_os_env:
                self.extra_env.update(os.environ)
            if self.include_kicad_env:
                self.extra_env.update(KiConf.kicad_env)
            # Get the text variables from the project
            self.text_vars = GS.load_pro_variables()
            self._first_pass = False
        # Expand text variables in all fields
        for f in comp.fields:
            new_value = expand_env(f.value, self.text_vars, self.extra_env)
            if new_value != f.value:
                comp.set_field(f.name, new_value)
                if GS.debug_level > 2:
                    logger.debug('ref: {} {}: {} -> {}'.format(comp.ref, f.name, f.value, new_value))
