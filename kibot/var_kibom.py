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
from .misc import DNF, DNC
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

    @staticmethod
    def basic_comp_is_fitted(value, config):
        """ Basic `fitted` criteria, no variants.
            value: component value (lowercase).
            config: content of the 'Config' field (lowercase). """
        # Check the value field first
        if value in DNF:
            return False
        # Empty value means part is fitted
        if not config:
            return True
        # Also support space separated list (simple cases)
        opts = config.split(" ")
        for opt in opts:
            if opt in DNF:
                return False
        # Normal separator is ","
        opts = config.split(",")
        for opt in opts:
            if opt in DNF:
                return False
        return True

    @staticmethod
    def basic_comp_is_fixed(value, config):
        """ Basic `fixed` criteria, no variants
            Fixed components shouldn't be replaced without express authorization.
            value: component value (lowercase).
            config: content of the 'Config' field (lowercase). """
        # Check the value field first
        if value in DNC:
            return True
        # Empty is not fixed
        if not config:
            return False
        # Also support space separated list (simple cases)
        opts = config.split(" ")
        for opt in opts:
            if opt in DNC:
                return True
        # Normal separator is ","
        opts = config.split(",")
        for opt in opts:
            if opt in DNC:
                return True
        return False

    @staticmethod
    def _base_filter(comps, f_config):
        """ Fill the `fixed` and `fitted` using the basic criteria.
            No variant is applied in this step. """
        logger.debug("- Generic KiBoM rules")
        for c in comps:
            value = c.value.lower()
            config = c.get_field_value(f_config).lower()
            c.fitted = KiBoM.basic_comp_is_fitted(value, config)
            if GS.debug_level > 2:
                logger.debug('ref: {} value: {} config: {} -> fitted {}'.
                             format(c.ref, value, config, c.fitted))
            c.fixed = KiBoM.basic_comp_is_fixed(value, config)

    def variant_comp_is_fitted(self, value, config):
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

    def filter(self, comps):
        logger.debug("Applying KiBoM style filter `{}`".format(self.name))
        self._base_filter(comps, self.config_field)
        logger.debug("- Variant specific rules")
        for c in comps:
            if not c.fitted:
                # Don't check if we already discarded it during the basic test
                continue
            value = c.value.lower()
            config = c.get_field_value(self.config_field).lower()
            c.fitted = self.variant_comp_is_fitted(value, config)
            if not c.fitted and GS.debug_level > 2:
                logger.debug('ref: {} value: {} config: {} variant: {} -> False'.
                             format(c.ref, value, config, self.variant))
