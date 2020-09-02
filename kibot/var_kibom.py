# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Implements the KiBoM variants mechanism.
"""
from .optionable import Optionable
from .gs import GS
from .macros import macros, document, variant_class  # noqa: F401
from . import log

logger = log.get_logger(__name__)


@variant_class
class KiBoM(BaseVariant):  # noqa: F821
    """ KiBoM variant style
        The Config field (configurable) contains a comma separated list of variant directives.
        -VARIANT excludes a component from VARIANT.
        +VARIANT includes the component only if we are using this variant. """
    def __init__(self):
        super().__init__()
        with document:
            self.config_field = 'Config'
            """ Name of the field used to clasify components """
            self.variant = Optionable
            """ [string|list(string)=''] Board variant(s) """

    def config(self):
        super().config()
        # Variants, ensure a list
        if isinstance(self.variant, type):
            self.variant = []
        elif isinstance(self.variant, str):
            if self.variant:
                self.variant = [self.variant]
            else:
                self.variant = []
        self.variant = [v.lower() for v in self.variant]
        # Config field must be lowercase
        self.config_field = self.config_field.lower()

    def _variant_comp_is_fitted(self, value, config):
        """ Apply the variants to determine if this component will be fitted.
            value: component value (lowercase).
            config: content of the 'Config' field (lowercase). """
        # Variants logic
        opts = config.split(",")
        # Only fit for ...
        exclusive = False
        for opt in opts:
            opt = opt.strip()
            # Options that start with '-' are explicitly removed from certain configurations
            if opt.startswith("-") and opt[1:] in self.variant:
                return False
            # Options that start with '+' are fitted only for certain configurations
            if opt.startswith("+"):
                exclusive = True
                if opt[1:] in self.variant:
                    return True
        # No match
        return not exclusive

    def filter(self, comps, reset=False):
        super().filter(comps, reset)
        logger.debug("Applying KiBoM style variants `{}`".format(self.name))
        for c in comps:
            if not (c.fitted and c.in_bom):
                # Don't check if we already discarded it
                continue
            value = c.value.lower()
            config = c.get_field_value(self.config_field).lower()
            c.fitted = self._variant_comp_is_fitted(value, config)
            if not c.fitted and GS.debug_level > 2:
                logger.debug('ref: {} value: {} config: {} variant: {} -> False'.
                             format(c.ref, value, config, self.variant))
