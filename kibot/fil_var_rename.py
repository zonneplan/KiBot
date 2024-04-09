# -*- coding: utf-8 -*-
# Copyright (c) 2020-2024 Salvador E. Tropea
# Copyright (c) 2020-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Description: Implements the VARIANT:FIELD=VALUE renamer to get FIELD=VALUE when VARIANT is in use.
from .gs import GS
from .macros import macros, document, filter_class  # noqa: F401
from . import log

logger = log.get_logger()


@filter_class
class Var_Rename(BaseFilter):  # noqa: F821
    """ Variant Renamer
        This filter implements the VARIANT:FIELD=VALUE renamer to get FIELD=VALUE when VARIANT is in use.
        As an example: a field named *V1:MPN* with value *1N4001* will change the field *MPN* to be
        *1N4001* when the variant in use is *V1*.
        Note that this mechanism can be used to change a footprint, i.e. *VARIANT:Footprint* assigned
        with *Diode_SMD:D_0805_2012Metric* will change the footprint when *VARIANT* is in use. Of course the
        footprints should be similar, or your PCB will become invalid """
    def __init__(self):
        super().__init__()
        self._is_transform = True
        with document:
            self.separator = ':'
            """ Separator used between the variant and the field name """
            self.variant_to_value = False
            """ Rename fields matching the variant to the value of the component """
            self.force_variant = ''
            """ Use this variant instead of the current variant. Useful for IBoM variants """

    def config(self, parent):
        super().config(parent)
        if not self.separator:
            self.separator = ':'

    def filter(self, comp):
        """ Look for fields containing VARIANT:FIELD used to change fields according to the variant """
        if self.force_variant:
            variants = [self.force_variant]
        else:
            variants = GS.variant
            if not variants:
                # No variant in use, nothing to do
                return
        for variant in variants:
            for name, value in comp.get_user_fields():
                res = name.strip().split(self.separator)
                if len(res) == 2:
                    f_variant = res[0].lower()
                    f_field = res[1].lower()
                    if f_variant == variant:
                        old_value = comp.get_field_value(f_field)
                        if GS.debug_level > 2:
                            logger.debug('ref: {} {}: {} -> {}'.
                                         format(comp.ref, f_field, old_value, value))
                        comp.set_field(f_field, value)
                        if f_field == 'footprint' and old_value != value:
                            # Ok, this is crazy, but we can change the footprint
                            comp._footprint_variant = True
                elif self.variant_to_value and name.lower() == variant:
                    if GS.debug_level > 2:
                        logger.debug('ref: {} value: {} -> {}'.format(comp.ref, comp.value, value))
                    comp.set_field('value', value)
