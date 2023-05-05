# -*- coding: utf-8 -*-
# Copyright (c) 2023 Salvador E. Tropea
# Copyright (c) 2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Description: Extracts information from the distributor spec and fills fields
import re
from .bom.xlsx_writer import get_spec
from .error import KiPlotConfigurationError
from .kiplot import look_for_output, run_output
from .misc import W_FLDCOLLISION
# from .gs import GS
from .optionable import Optionable
from .macros import macros, document, filter_class  # noqa: F401
from . import log

logger = log.get_logger()


class SpecOptions(Optionable):
    """ A spec to copy """
    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.spec = Optionable
            """ [string|list(string)=''] *Name/s of the source spec/s """
            self.field = ''
            """ *Name of the destination field """
            self.policy = 'overwrite'
            """ [overwrite,update,new] Controls the behavior of the copy mechanism.
                `overwrite` always copy the spec value,
                `update` copy only if the field already exist,
                `new` copy only if the field doesn't exist. """
            self.collision = 'warning'
            """ [warning,error,ignore] How to report a collision between the current value and the new value """
            self.compare = 'plain'
            """ [plain,smart] How we compare the current value to determine a collision.
                `plain` is a strict comparison. `smart` tries to extract any number and compare it """
        self._field_example = 'RoHS'
        self._spec_example = 'rohs_status'

    def config(self, parent):
        super().config(parent)
        if not self.field:
            raise KiPlotConfigurationError("Missing or empty `field` in spec_to_field filter ({})".format(str(self._tree)))
        if not self.spec:
            raise KiPlotConfigurationError("Missing or empty `spec` in spec_to_field filter ({})".format(str(self._tree)))
        self.spec = self.force_list(self.spec)


@filter_class
class Spec_to_Field(BaseFilter):  # noqa: F821
    """ Spec_to_Field
        This filter extracts information from the specs obtained from component distributors
        and fills fields.
        I.e. create a field with the RoHS status of a component.
        In order to make it work you must be able to get prices using the KiCost options of
        the `bom` output. Make sure you can do this before trying to use this filter.
        Usage [example](https://inti-cmnb.github.io/kibot-examples-1/spec_to_field/) """
    def __init__(self):
        super().__init__()
        self._is_transform = True
        with document:
            self.from_output = ''
            """ *Name of the output used to collect the specs.
                Currently this must be a `bom` output with KiCost enabled and a distributor that returns specs """
            self.specs = SpecOptions
            """ [list(dict)|dict] *One or more specs to be copied """
        self._from = None

    def config(self, parent):
        super().config(parent)
        if not self.from_output:
            raise KiPlotConfigurationError("You must specify an output that collected the specs")
        if isinstance(self.specs, type):
            raise KiPlotConfigurationError("At least one spec must be provided ({})".format(str(self._tree)))
        if isinstance(self.specs, SpecOptions):
            self.specs = [self.specs]

    def compare(self, cur_val, spec_val, how):
        cur_val = cur_val.lower().strip()
        spec_val = spec_val.lower().strip()
        if how == 'plain':
            logger.debugl(3, f"  - Compare {cur_val} == {spec_val}")
            return cur_val == spec_val
        # smart
        cur_match = re.match(r'(.*?)(\d+)(.*?)', cur_val)
        if cur_match:
            spec_match = re.match(r'(.*?)(\d+)(.*?)', spec_val)
            if spec_match:
                logger.debugl(3, f"  - Compare {int(cur_match.group(2))} == {int(spec_match.group(2))}")
                return int(cur_match.group(2)) == int(spec_match.group(2))
        logger.debugl(3, f"  - Compare {cur_val} == {spec_val}")
        return cur_val == spec_val

    def solve_from(self):
        if self._from is not None:
            return
        # Check the renderer output is valid
        out = look_for_output(self.from_output, 'from_output', self._parent, {'bom'})
        if not out._done:
            run_output(out)
        self._from = out

    def filter(self, comp):
        self.solve_from()
        for d, dd in comp.kicost_part.dd.items():
            logger.error(f"{d} {dd.extra_info}")
        for s in self.specs:
            field = s.field.lower()
            spec_name = []
            spec_val = []
            for sp in s.spec:
                name, val = get_spec(comp.kicost_part, sp)
                if name:
                    spec_name.append(name)
                if val:
                    spec_val.append(val)
            spec_name = ','.join(spec_name)
            spec_val = ' '.join(spec_val)
            if not spec_name or not spec_val:
                # No info
                continue
            has_field = comp.is_field(field)
            cur_val = comp.get_field_value(field) if has_field else None
            if cur_val:
                if cur_val == spec_val:
                    # Already there
                    continue
                if not self.compare(cur_val, spec_val, s.compare):
                    # Collision
                    desc = "{} field `{}` collision, has `{}`, found `{}`".format(comp.ref, s.field, cur_val, spec_val)
                    if s.collision == 'warning':
                        logger.warning(W_FLDCOLLISION+desc)
                    elif s.collision == 'error':
                        raise KiPlotConfigurationError(desc)
            if s.policy == 'overwrite' or (self.p == 'update' and has_field) or (s.policy == 'new' and not has_field):
                comp.set_field(s.field, spec_val)
                logger.debugl(2, "- {} {}: {} ({})".format(comp.ref, s.field, spec_val, spec_name))
