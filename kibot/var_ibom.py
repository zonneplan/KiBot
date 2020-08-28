# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Implements the IBoM variants mechanism.
"""
from .optionable import Optionable
from .gs import GS
from .macros import macros, document, variant_class  # noqa: F401
from . import log

logger = log.get_logger(__name__)


@variant_class
class IBoM(BaseVariant):  # noqa: F821
    """ IBoM variant style
        The Config field (configurable) contains a value.
        If this value matches with a value in the whitelist is included.
        If this value matches with a value in the blacklist is excluded. """
    def __init__(self):
        super().__init__()
        with document:
            self.variant_field = 'Config'
            """ Name of the field that stores board variant for component """
            self.variants_blacklist = Optionable
            """ [string|list(string)=''] List of board variants to exclude from the BOM """
            self.variants_whitelist = Optionable
            """ [string|list(string)=''] List of board variants to include in the BOM """
            self.blacklist = Optionable
            """ [string|list(string)=''] List of comma separated blacklisted components or prefixes with *. E.g. 'X1,MH*' """
            self.blacklist_empty_val = False
            """ Blacklist components with empty value """
            self.dnp_field = ''
            """ Name of the extra field that indicates do not populate status.
                Components with this field not empty will be blacklisted """

    @staticmethod
    def _force_list(val):
        if isinstance(val, type):
            # Not used
            val = []
        elif isinstance(val, str):
            # A string
            if val:
                val = [v.strip() for v in val.split(',')]
            else:
                # Empty string
                val = []
        return val

    def config(self):
        super().config()
        self.variants_blacklist = self._force_list(self.variants_blacklist)
        self.variants_whitelist = self._force_list(self.variants_whitelist)
        self.blacklist = self._force_list(self.blacklist)

    def skip_component(self, c):
        """ Skip blacklisted components.
            This is what IBoM does internally """
        if c.ref in self.blacklist:
            return True
        if c.ref_prefix + '*' in self.blacklist:
            return True
        # Remove components with empty value
        if self.blacklist_empty_val and c.value in ['', '~']:
            return True
        # Skip virtual components if needed
        # TODO: We currently lack this information
        # if config.blacklist_virtual and m.attr == 'Virtual':
        #     return True
        # Skip components with dnp field not empty
        if self.dnp_field and c.get_field_value(self.dnp_field):
            return True
        # Apply variants white/black lists
        if self.variant_field:
            ref_variant = c.get_field_value(self.variant_field).lower()
            # skip components with wrong variant field
            if self.variants_whitelist and ref_variant not in self.variants_whitelist:
                return True
            if self.variants_blacklist and ref_variant and ref_variant in self.variants_blacklist:
                return True
        return False

    def filter(self, comps):
        logger.debug("Applying IBoM style filter `{}`".format(self.name))
        # Make black/white lists case insensitive
        self.variants_whitelist = [v.lower() for v in self.variants_whitelist]
        self.variants_blacklist = [v.lower() for v in self.variants_blacklist]
        # Apply to all the components
        for c in comps:
            c.fitted = not self.skip_component(c)
            c.fixed = False
            if not c.fitted and GS.debug_level > 2:
                logger.debug('ref: {} value: {} -> False'.format(c.ref, c.value))
