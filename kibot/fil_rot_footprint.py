# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Description: Implements a filter to rotate footprints.
#              This is inspired in JLCKicadTools by Matthew Lai.
#              I latter added more information from bennymeg/JLC-Plugin-for-KiCad
from math import sin, cos, radians
from re import compile
from .gs import GS
from .optionable import Optionable
from .error import KiPlotConfigurationError
from .macros import macros, document, filter_class  # noqa: F401
from .misc import W_BADANGLE, W_BADOFFSET
from . import log

logger = log.get_logger()


# Known rotations for JLC
DEFAULT_ROTATIONS = [["^R_Array_Convex_", 90.0],
                     ["^R_Array_Concave_", 90.0],
                     ["^SOT-223", 180.0],
                     ["^SOT-23", 180.0],
                     ["^D_SOT-23", 180.0],
                     ["^TSOT-23", 180.0],
                     ["^SOT-353", 180.0],
                     ["^QFN-", 270.0],
                     ["^LQFP-", 270.0],
                     ["^TQFP-", 270.0],
                     ["^SOP-(?!18_)", 270.0],
                     ["^MSOP-", 270.0],
                     ["^TSSOP-", 270.0],
                     ["^DFN-", 270.0],
                     ["^SOIC-", 270.0],
                     # ["^SOP-18_", 0],
                     ["^VSSOP-10_", 270.0],
                     ["^CP_EIA-", 180.0],
                     ["^CP_Elec_", 180.0],
                     ["^C_Elec_", 180.0],
                     ["^LED_WS2812B_PLCC4", 180.0],
                     ["^(.*?_|V)?QFN-(16|20|24|28|40)(-|_|$)", 270.0],
                     ["^Bosch_LGA-", 90.0],
                     ["^PowerPAK_SO-8_Single", 270.0],
                     ["^HTSSOP-", 270.0],
                     ]
DEFAULT_ROT_FIELDS = ['JLCPCB Rotation Offset', 'JLCRotOffset']
DEFAULT_OFFSET_FIELDS = ['JLCPCB Position Offset', 'JLCPosOffset']


@filter_class
class Rot_Footprint(BaseFilter):  # noqa: F821
    """ Footprint Rotator
        This filter can rotate footprints, used for the positions file generation.
        Some manufacturers use a different rotation than KiCad.
        The `JLCPCB Rotation Offset` and `JLCPCB Position Offset` fields can be used to adjust special cases.
        The internal `_rot_footprint` filter implements the simplest case """
    def __init__(self):
        super().__init__()
        self._is_transform = True
        with document:
            self.extend = True
            """ Extends the internal list of rotations with the one provided.
                Otherwise just use the provided list """
            self.negative_bottom = True
            """ Rotation for bottom components is computed via subtraction as `(component rot - angle)` """
            self.invert_bottom = False
            """ Rotation for bottom components is negated, resulting in either: `(- component rot - angle)`
                or when combined with `negative_bottom`, `(angle - component rot)` """
            self.mirror_bottom = False
            """ The original component rotation for components in the bottom is mirrored before applying
                the adjust so you get `(180 - component rot + angle)`. This is used by JLCPCB """
            self.rotations = Optionable
            """ [list(list(string))] A list of pairs regular expression/rotation.
                Components matching the regular expression will be rotated the indicated angle """
            self.skip_bottom = False
            """ Do not rotate components on the bottom """
            self.skip_top = False
            """ Do not rotate components on the top """
            self.rot_fields = Optionable
            """ [string|list(string)='JLCPCB Rotation Offset,JLCRotOffset'] List of fields that can contain a rotation offset.
                The optional fields can contain a counter-clockwise orientation offset in degrees.
                This concept is from the bennymeg/JLC-Plugin-for-KiCad tool """
            self.offset_fields = Optionable
            """ [string|list(string)='JLCPCB Position Offset,JLCPosOffset'] List of fields that can contain a position offset.
                The optional fields can contain a comma separated x,y position offset.
                This concept is from the bennymeg/JLC-Plugin-for-KiCad tool """
            self.bennymeg_mode = True
            """ Implements the `rot_fields` and `offset_fields` in the same way that the bennymeg/JLC-Plugin-for-KiCad tool.
                Note that the computation for bottom rotations is wrong, forcing the user to uses arbitrary rotations.
                The correct computation is `(180 - component rot) + angle` but the plugin does `180 - (component rot + angle)`.
                This option forces the wrong computation for compatibility """

    def config(self, parent):
        super().config(parent)
        self._rot = []
        if isinstance(self.rotations, list):
            for r in self.rotations:
                if len(r) != 2:
                    raise KiPlotConfigurationError("Each regex/angle pair must contain exactly two values, not {} ({})".
                                                   format(len(r), r))
                regex = compile(r[0])
                try:
                    angle = float(r[1])
                except ValueError:
                    raise KiPlotConfigurationError("The second value in the regex/angle pairs must be a number, not {}".
                                                   format(r[1]))
                self._rot.append([regex, angle])
        if self.extend:
            for regex_str, angle in DEFAULT_ROTATIONS:
                self._rot.append([compile(regex_str), angle])
        if not self._rot:
            raise KiPlotConfigurationError("No rotations provided")
        self.rot_fields = self.force_list(self.rot_fields, default=DEFAULT_ROT_FIELDS)
        self.offset_fields = self.force_list(self.offset_fields, default=DEFAULT_OFFSET_FIELDS)

    def apply_rotation_angle(self, comp, angle, bennymeg_mode=False):
        old_footprint_rot = comp.footprint_rot
        if comp.bottom:
            # Apply adjusts for bottom components
            if bennymeg_mode and self.bennymeg_mode:
                # Compatible with https://github.com/bennymeg/JLC-Plugin-for-KiCad/
                # Wrong! The real value is (180-comp.footprint_rot)+angle and not
                #                           180-(comp.footprint_rot+angle)
                comp.footprint_rot = (comp.footprint_rot + angle) % 360.0
                comp.offset_footprint_rot = old_footprint_rot
                comp.footprint_rot = (540.0 - comp.footprint_rot) % 360.0
            else:
                if self.mirror_bottom:
                    comp.footprint_rot = 180 - comp.footprint_rot
                if self.negative_bottom:
                    comp.footprint_rot -= angle
                else:
                    comp.footprint_rot += angle
                if self.invert_bottom:
                    comp.footprint_rot = -comp.footprint_rot
                comp.offset_footprint_rot = old_footprint_rot
        else:
            comp.footprint_rot += angle
            comp.offset_footprint_rot = old_footprint_rot
        comp.footprint_rot = comp.footprint_rot % 360
        if GS.debug_level > 2:
            logger.debug('Rotating ref: {} {}: {} -> {}'.
                         format(comp.ref, comp.footprint, old_footprint_rot, comp.footprint_rot))

    def apply_field_rotation(self, comp):
        for f in self.rot_fields:
            value = comp.get_field_value(f)
            if value:
                try:
                    angle = float(value)
                except ValueError:
                    logger.warning(f'{W_BADANGLE}Wrong angle `{value}` in {f} field of {comp.ref}')
                    angle = 0
                self.apply_rotation_angle(comp, angle, bennymeg_mode=True)
                return

    def apply_rotation(self, comp):
        if self.apply_field_rotation(comp):
            return
        # Try with the regex
        for regex, angle in self._rot:
            if regex.search(comp.footprint):
                self.apply_rotation_angle(comp, angle)
                return
        # No rotation, apply 0 to apply bottom adjusts
        self.apply_rotation_angle(comp, 0)

    def apply_field_offset(self, comp):
        for f in self.offset_fields:
            value = comp.get_field_value(f)
            if value:
                try:
                    pos_offset_x = float(value.split(",")[0])
                    pos_offset_y = float(value.split(",")[1])
                except ValueError:
                    logger.warning(f'{W_BADOFFSET}Wrong offset `{value}` in {f} field of {comp.ref}')
                    return
                rotation = radians(comp.offset_footprint_rot)
                rsin = sin(rotation)
                rcos = cos(rotation)
                comp.pos_offset_x = pos_offset_x * rcos - pos_offset_y * rsin
                comp.pos_offset_y = pos_offset_x * rsin + pos_offset_y * rcos
                return

    def filter(self, comp):
        """ Apply the rotation """
        logger.error(f"{self.invert_bottom} {self.mirror_bottom}")
        if (self.skip_top and not comp.bottom) or (self.skip_bottom and comp.bottom):
            # Component should be excluded
            return
        self.apply_rotation(comp)
        self.apply_field_offset(comp)
