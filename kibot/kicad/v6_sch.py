# -*- coding: utf-8 -*-
# Copyright (c) 2021 Salvador E. Tropea
# Copyright (c) 2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
KiCad v6 Schematic format.
A basic implementation of the .kicad_sch file format.
Currently oriented to collect the components for the BoM.
Documentation: https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/
"""
# Encapsulate file/line
import os
from copy import deepcopy
from collections import OrderedDict
from ..gs import GS
from .. import log
from ..misc import W_NOLIB, W_UNKFLD, W_MISSCMP
from .v5_sch import SchError, SchematicComponent, Schematic
from .sexpdata import load, SExpData, Symbol

logger = log.get_logger(__name__)


def _check_is_symbol_list(e, allow_orphan_symbol=[]):
    # Each entry is a list
    if not isinstance(e, list):
        if isinstance(e, Symbol):
            name = e.value()
            if name in allow_orphan_symbol:
                return name
            raise SchError('Orphan symbol `{}`'.format(e.value()))
        else:
            raise SchError('Orphan data `{}`'.format(e))
    # The first element is a symbol
    if not isinstance(e[0], Symbol):
        raise SchError('Orphan data `{}`'.format(e[0]))
    return e[0].value()


def _check_len(items, pos, name):
    if len(items) < pos+1:
        raise SchError('Missing argument {} in `{}`'.format(pos, name))
    return items[pos]


def _check_len_total(items, num, name):
    if len(items) != num:
        raise SchError('Wrong number of attributes for {} `{}`'.format(name, items))


def _check_symbol(items, pos, name):
    value = _check_len(items, pos, name)
    if not isinstance(value, Symbol):
        raise SchError('{} is not a Symbol `{}`'.format(name, value))
    return value.value()


def _check_hide(items, pos, name):
    value = _check_symbol(items, pos, name + ' hide')
    if value != 'hide':
        raise SchError('Found Symbol `{}` when `hide` expected'.format(value))
    return True


def _check_integer(items, pos, name):
    value = _check_len(items, pos, name)
    if not isinstance(value, int):
        raise SchError('{} is not an integer `{}`'.format(name, value))
    return value


def _check_float(items, pos, name):
    value = _check_len(items, pos, name)
    if not isinstance(value, (float, int)):
        raise SchError('{} is not a float `{}`'.format(name, value))
    return value


def _check_str(items, pos, name):
    value = _check_len(items, pos, name)
    if not isinstance(value, str):
        raise SchError('{} is not a string `{}`'.format(name, value))
    return value


def _check_symbol_value(items, pos, name, sym):
    value = _check_len(items, pos, name)
    if not isinstance(value, list) or not isinstance(value[0], Symbol) or value[0].value() != sym:
        raise SchError('Missing `{}` in `{}`'.format(sym, name))
    return value


def _check_symbol_float(items, pos, name, sym):
    name += ' ' + sym
    values = _check_symbol_value(items, pos, name, sym)
    return _check_float(values, 1, name)


def _check_symbol_int(items, pos, name, sym):
    name += ' ' + sym
    values = _check_symbol_value(items, pos, name, sym)
    return _check_integer(values, 1, name)


def _check_symbol_str(items, pos, name, sym):
    name += ' ' + sym
    values = _check_symbol_value(items, pos, name, sym)
    return _check_str(values, 1, name)


def _get_offset(items, pos, name):
    value = _check_symbol_value(items, pos, name, 'offset')
    return _check_float(value, 1, 'offset')


def _get_yes_no(items, pos, name):
    sym = _check_symbol(items, pos, name)
    return sym == 'yes'


def _get_id(items, pos, name):
    value = _check_symbol_value(items, pos, name, 'id')
    return _check_integer(value, 1, 'id')


def _get_at(items, pos, name):
    value = _check_symbol_value(items, pos, name, 'at')
    angle = 0
    if len(value) > 3:
        angle = _check_float(value, 3, 'at angle')
    return _check_float(value, 1, 'at x'), _check_float(value, 2, 'at y'), angle


class Point(object):
    def __init__(self, items):
        super().__init__()
        self.x = _check_float(items, 1, 'x coord')
        self.y = _check_float(items, 2, 'y coord')

    @staticmethod
    def parse(items):
        return Point(items)


def _get_xy(items):
    if len(items) != 3:
        raise SchError('Point definition with wrong args (`{}`)'.format(items))
    return Point.parse(items)


def _get_points(items):
    points = []
    for i in items[1:]:
        i_type = _check_is_symbol_list(i)
        if i_type == 'xy':
            points.append(_get_xy(i))
        else:
            raise SchError('Unknown points attribute `{}`'.format(i))
    return points


class FontEffects(object):
    """ Class used to describe text attributes """
    def __init__(self):
        super().__init__()
        self.hide = False
        self.w = self.h = 1.27
        self.thickness = None
        self.bold = self.italic = False
        self.hjustify = self.vjustify = 'C'
        self.mirror = False

    @staticmethod
    def parse_font(items):
        w = h = 1.27
        thickness = None
        bold = italic = False
        for i in items[1:]:
            if isinstance(i, Symbol):
                name = i.value()
                if name == 'bold':
                    bold = True
                elif name == 'italic':
                    italic = True
                else:
                    raise SchError('Unknown font effect attribute `{}`'.format(name))
            else:  # A list
                i_type = _check_is_symbol_list(i)
                if i_type == 'size':
                    w = _check_float(i, 1, 'font width')
                    h = _check_float(i, 2, 'font height')
                elif i_type == 'thickness':
                    thickness = _check_float(i, 1, 'font thickness')
                else:
                    raise SchError('Unknown font effect attribute `{}`'.format(i))
        return w, h, thickness, bold, italic

    @staticmethod
    def parse_justify(items):
        h = v = 'C'
        mirror = False
        for i in items[1:]:
            if isinstance(i, Symbol):
                name = i.value()
                if name == 'left':
                    h = 'L'
                elif name == 'right':
                    h = 'R'
                elif name == 'top':
                    h = 'T'
                elif name == 'bottom':
                    h = 'B'
                elif name == 'mirror':
                    mirror = True
                else:
                    raise SchError('Unknown font effect attribute `{}`'.format(name))
            else:  # A list
                raise SchError('Unknown font effect attribute `{}`'.format(i))
        return h, v, mirror

    @staticmethod
    def parse(items):
        o = FontEffects()
        for c, i in enumerate(items[1:]):
            if isinstance(i, Symbol):
                # Only hide exists
                o.hide = _check_hide(items, c+1, 'font effect')
            elif isinstance(i, list):
                i_type = _check_is_symbol_list(i)
                if i_type == 'font':
                    o.w, o.h, o.thickness, o.bold, o.italic = FontEffects.parse_font(i)
                elif i_type == 'justify':
                    o.hjustify, o.vjustify, o.mirror = FontEffects.parse_justify(i)
                else:
                    raise SchError('Unknown font effect attribute `{}`'.format(i))
        return o


class Color(object):
    def __init__(self, items):
        super().__init__()
        self.r = _check_integer(items, 1, 'red color')
        self.g = _check_integer(items, 2, 'green color')
        self.b = _check_integer(items, 3, 'blue color')
        # Sheet sheet.fill.color is float ...
        self.a = _check_float(items, 4, 'alpha color')

    @staticmethod
    def parse(items):
        return Color(items)


class Stroke(object):
    def __init__(self):
        super().__init__()
        self.width = 0
        self.type = 'default'
        self.color = None

    @staticmethod
    def parse(items):
        stroke = Stroke()
        for i in items[1:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'width':
                stroke.width = _check_float(i, 1, 'stroke width')
            elif i_type == 'type':
                stroke.type = _check_symbol(i, 1, 'stroke type')
            elif i_type == 'color':
                stroke.color = Color.parse(i)
            else:
                raise SchError('Unknown stroke attribute `{}`'.format(i))
        return stroke


class Fill(object):
    def __init__(self):
        super().__init__()
        self.type = 'none'
        self.color = None

    @staticmethod
    def parse(items):
        fill = Fill()
        for i in items[1:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'type':
                fill.type = _check_symbol(i, 1, 'fill type')
            elif i_type == 'color':
                # Not documented, found in sheet.fill
                fill.color = Color.parse(i)
            else:
                raise SchError('Unknown fill attribute `{}`'.format(i))
        return fill


class DrawArcV6(object):
    def __init__(self):
        super().__init__()
        self.start = None
        self.mid = None
        self.end = None
        self.stroke = None
        self.fill = None

    @staticmethod
    def parse(items):
        arc = DrawArcV6()
        for i in items[1:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'start':
                arc.start = _get_xy(i)
            elif i_type == 'mid':
                arc.mid = _get_xy(i)
            elif i_type == 'end':
                arc.end = _get_xy(i)
            elif i_type == 'stroke':
                arc.stroke = Stroke.parse(i)
            elif i_type == 'fill':
                arc.fill = Fill.parse(i)
            else:
                raise SchError('Unknown arc attribute `{}`'.format(i))
        return arc


class DrawCircleV6(object):
    def __init__(self):
        super().__init__()
        self.center = None
        self.radius = 0
        self.stroke = None
        self.fill = None

    @staticmethod
    def parse(items):
        circle = DrawCircleV6()
        for i in items[1:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'center':
                circle.center = _get_xy(i)
            elif i_type == 'radius':
                circle.radius = _check_float(i, 1, 'circle radius')
            elif i_type == 'stroke':
                circle.stroke = Stroke.parse(i)
            elif i_type == 'fill':
                circle.fill = Fill.parse(i)
            else:
                raise SchError('Unknown circle attribute `{}`'.format(i))
        return circle


class DrawRectangleV6(object):
    def __init__(self):
        super().__init__()
        self.start = None
        self.end = None
        self.stroke = None
        self.fill = None

    @staticmethod
    def parse(items):
        rectangle = DrawRectangleV6()
        for i in items[1:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'start':
                rectangle.start = _get_xy(i)
            elif i_type == 'end':
                rectangle.end = _get_xy(i)
            elif i_type == 'stroke':
                rectangle.stroke = Stroke.parse(i)
            elif i_type == 'fill':
                rectangle.fill = Fill.parse(i)
            else:
                raise SchError('Unknown rectangle attribute `{}`'.format(i))
        return rectangle


class DrawCurve(object):
    """ Qubic Bezier """
    def __init__(self):
        super().__init__()
        self.points = []
        self.stroke = None
        self.fill = None

    @staticmethod
    def parse(items):
        curve = DrawCurve()
        for i in items[1:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'pts':
                curve.points = _get_points(i)
            elif i_type == 'stroke':
                curve.stroke = Stroke.parse(i)
            elif i_type == 'fill':
                curve.fill = Fill.parse(i)
            else:
                raise SchError('Unknown curve attribute `{}`'.format(i))
        return curve


class DrawPolyLine(object):
    def __init__(self):
        super().__init__()
        self.points = []
        self.stroke = None
        self.fill = None

    @staticmethod
    def parse(items):
        line = DrawPolyLine()
        for i in items[1:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'pts':
                line.points = _get_points(i)
            elif i_type == 'stroke':
                line.stroke = Stroke.parse(i)
            elif i_type == 'fill':
                line.fill = Fill.parse(i)
            else:
                raise SchError('Unknown polyline attribute `{}`'.format(i))
        return line


class DrawTextV6(object):
    def __init__(self):
        super().__init__()
        self.text = None
        self.x = self.y = self.ang = 0
        self.effects = None

    @staticmethod
    def parse(items):
        text = DrawTextV6()
        text.text = _check_str(items, 1, 'text')
        text.x, text.y, text.ang = _get_at(items, 2, 'text')
        text.effects = _get_effects(items, 3, 'text')
        return text


def _get_effects(items, pos, name):
    values = _check_symbol_value(items, pos, name, 'effects')
    return FontEffects.parse(values)


class PinV6(object):
    def __init__(self):
        super().__init__()
        self.type = self.gtype = self.name = self.number = ''
        self.pos_x = self.pos_y = self.ang = self.len = 0
        self.name_effects = self.number_effects = None
        self.hide = False

    @staticmethod
    def parse(items):
        name = 'pin'
        pin = PinV6()
        pin.type = _check_symbol(items, 1, name+' type')
        pin.gtype = _check_symbol(items, 2, name+' style')
        for c, i in enumerate(items[3:]):
            i_type = _check_is_symbol_list(i, allow_orphan_symbol=['hide'])
            if i_type == 'at':
                pin.pos_x, pin.pos_y, pin.ang = _get_at(items, c+3, name)
            elif i_type == 'length':
                pin.len = _check_float(i, 1, name+' length')
            elif i_type == 'hide':
                # Not documented yet
                pin.hide = True
            elif i_type == 'name':
                pin.name = _check_str(i, 1, name+' name')
                pin.name_effects = _get_effects(i, 2, name+' name')
            elif i_type == 'number':
                pin.number = _check_str(i, 1, name+' number')
                pin.number_effects = _get_effects(i, 2, name+' number')
            else:
                raise SchError('Unknown pin attribute `{}`'.format(i))
        return pin


class SchematicFieldV6(object):
    # Fixed ids:
    # 0 Reference
    # 1 Value
    # 2 Footprint
    # 3 Datasheet
    # Reserved names: ki_keywords, ki_description, ki_locked, ki_fp_filters

    @staticmethod
    def parse(items):
        if len(items) != 6:
            _check_len_total(items, 5, 'property')
        field = SchematicFieldV6()
        field.name = _check_str(items, 1, 'field name')
        field.value = _check_str(items, 2, 'field value')
        field.number = _get_id(items, 3, 'field id')
        field.x, field.y, field.ang = _get_at(items, 4, 'field')
        if len(items) > 5:
            field.effects = _get_effects(items, 5, 'field')
        else:
            field.effects = None
        return field


class LibComponent(object):
    def __init__(self):
        super().__init__()
        self.pin_numbers_hide = None
        self.pin_names_hide = None
        self.pin_names_offset = None
        self.in_bom = False
        self.on_board = False
        self.is_power = False
        self.unit = 0
        self.draw = []
        self.fields = []
        self.dfields = {}

    @staticmethod
    def load(c, project, is_unit=False):  # noqa: C901
        if not isinstance(c, list):
            raise SchError('Library component definition is not a list')
        if len(c) < 3:
            raise SchError('Truncated library component definition (len<3)')
        if not isinstance(c[0], Symbol) or c[0].value() != 'symbol':
            raise SchError('Library component definition is of wrong type')
        comp = LibComponent()
        comp.project = project
        # First argument is the LIB:NAME
        comp.lib_id = comp.name = _check_str(c, 1, 'name')
        res = comp.name.split(':')
        comp.lib = None
        if len(res) == 2:
            comp.name = res[1]
            comp.lib = res[0]
            # libs[comp.lib] = None
        else:
            if not is_unit:
                logger.warning(W_NOLIB + "Component `{}` doesn't specify its library".format(comp.name))
        comp.units = []
        comp.pins = []
        # Variable list
        for i in c[2:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'pin_numbers':
                comp.pin_numbers_hide = _check_hide(i, 1, i_type)
            elif i_type == 'pin_names':
                value = _check_len(i, 1, i_type)
                index = 1
                if isinstance(value, list):
                    comp.pin_names_offset = _get_offset(i, 1, i_type)
                    index = 2
                comp.pin_names_hide = None
                try:
                    comp.pin_names_hide = _check_symbol(i, index, i_type)
                except SchError:
                    # Optional
                    pass
            elif i_type == 'in_bom':
                comp.in_bom = _get_yes_no(i, 1, i_type)
            elif i_type == 'on_board':
                comp.on_board = _get_yes_no(i, 1, i_type)
            elif i_type == 'power':
                # Not yet documented
                comp.is_power = True
            # SYMBOL_PROPERTIES...
            elif i_type == 'property':
                field = SchematicFieldV6.parse(i)
                comp.fields.append(field)
                comp.dfields[field.name.lower()] = field
            # GRAPHIC_ITEMS...
            elif i_type == 'arc':
                comp.draw.append(DrawArcV6.parse(i))
            elif i_type == 'circle':
                comp.draw.append(DrawCircleV6.parse(i))
            elif i_type == 'gr_curve':
                comp.draw.append(DrawCurve.parse(i))
            elif i_type == 'polyline':
                comp.draw.append(DrawPolyLine.parse(i))
            elif i_type == 'rectangle':
                comp.draw.append(DrawRectangleV6.parse(i))
            elif i_type == 'text':
                comp.draw.append(DrawTextV6.parse(i))
            # PINS...
            elif i_type == 'pin':
                comp.pins.append(PinV6.parse(i))
            # UNITS...
            elif i_type == 'symbol':
                obj = LibComponent.load(i, project, is_unit=True)
                comp.units.append(obj)
                # logger.warning('Unit: '+str(obj))
            else:
                raise SchError('Unknown symbol attribute `{}`'.format(i))
        return comp


class SchematicComponentV6(SchematicComponent):
    def __init__(self):
        super().__init__()
        self.in_bom = False
        self.on_board = False
        self.pins = OrderedDict()
        self.unit = 0
        self.ref = None

    def set_ref(self, ref):
        self.ref = ref
        # Separate the reference in its components
        m = SchematicComponent.ref_re.match(ref)
        if not m:
            raise SchError('Malformed component reference `{}`'.format(ref))
        self.ref_prefix, self.ref_suffix = m.groups()

    def set_footprint(self, fp):
        res = fp.split(':')
        cres = len(res)
        if cres == 1:
            self.footprint = res[0]
            self.footprint_lib = None
        elif cres == 2:
            self.footprint_lib = res[0]
            self.footprint = res[1]
        else:
            raise SchError('Footprint with more than one colon (`{}`)'.format(fp))

    @staticmethod
    def load(c, project, parent):
        if not isinstance(c, list):
            raise SchError('Component definition is not a list')
        if len(c) < 7:
            raise SchError('Truncated component definition (len<7)')
        if not isinstance(c[0], Symbol) or c[0].value() != 'symbol':
            raise SchError('Component definition is of wrong type')
        comp = SchematicComponentV6()
        comp.project = project
        comp.sheet_path_h = parent.sheet_path_h
        name = 'component'
        # First argument is the LIB:NAME
        comp.lib_id = comp.name = _check_symbol_str(c, 1, name, 'lib_id')
        res = comp.name.split(':')
        comp.lib = None
        if len(res) == 2:
            comp.name = res[1]
            comp.lib = res[0]
            # libs[comp.lib] = None
        else:
            logger.warning(W_NOLIB + "Component `{}` doesn't specify its library".format(comp.name))
        # 2 The position
        comp.x, comp.y, comp.ang = _get_at(c, 2, name)
        # 3 Unit
        # Variable list
        for i in c[4:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'unit':
                # This is documented as mandatory, but isn't always there
                comp.unit = _check_integer(i, 1, name+' unit')
            elif i_type == 'in_bom':
                comp.in_bom = _get_yes_no(i, 1, i_type)
            elif i_type == 'on_board':
                comp.on_board = _get_yes_no(i, 1, i_type)
            elif i_type == 'uuid':
                comp.uuid = _check_symbol(i, 1, name + ' uuid')
            # SYMBOL_PROPERTIES...
            elif i_type == 'property':
                field = SchematicFieldV6.parse(i)
                name_lc = field.name.lower()
                # Add to the global collection
                if name_lc not in parent.fields_lc:
                    parent.fields.append(field.name)
                    parent.fields_lc.add(name_lc)
                # Add to the component
                comp.add_field(field)
                if field.number == 3:
                    # Reference, Value and Footprint are defined by the instance.
                    # But datasheet must be transferred from this field.
                    comp.datasheet = field.value
            # PINS...
            elif i_type == 'pin':
                pin_name = _check_str(i, 1, name + 'pin name')
                pin_uuid = _get_uuid(i, 2, name)
                comp.pins[pin_name] = pin_uuid
        # Fake 'Part' field
        field = SchematicFieldV6()
        field.name = 'part'
        field.value = comp.name
        field.number = -1
        comp.add_field(field)
        return comp


def _get_uuid(items, pos, where):
    values = _check_symbol_value(items, pos, where + ' uuid', 'uuid')
    return _check_symbol(values, 1, where + ' uuid')


class Junction(object):
    @staticmethod
    def parse(items):
        _check_len_total(items, 5, 'junction')
        jun = Junction()
        jun.pos_x, jun.pos_y, jun.ang = _get_at(items, 1, 'junction')
        jun.diameter = _check_symbol_float(items, 2, 'junction', 'diameter')
        jun.color = Color.parse(items[3])
        jun.uuid = _get_uuid(items, 4, 'junction')
        return jun


class NoConnect(object):
    @staticmethod
    def parse(items):
        _check_len_total(items, 3, 'no_connect')
        nocon = NoConnect()
        nocon.pos_x, nocon.pos_y, nocon.ang = _get_at(items, 1, 'no connect')
        nocon.uuid = _get_uuid(items, 2, 'no connect')
        return nocon


class BusEntry(object):
    @staticmethod
    def parse(items):
        _check_len_total(items, 5, 'bus entry')
        buse = BusEntry()
        buse.pos_x, buse.pos_y, buse.ang = _get_at(items, 1, 'bus entry')
        values = _check_symbol_value(items, 2, 'bus entry size', 'size')
        buse.size = _get_xy(values)
        buse.stroke = Stroke.parse(items[3])
        buse.uuid = _get_uuid(items, 4, 'bus entry')
        return buse


class SchematicWireV6(object):
    @staticmethod
    def parse(items, name):
        _check_len_total(items, 4, name)
        wire = SchematicWireV6()
        wire.points = _get_points(items[1])
        wire.stroke = Stroke.parse(items[2])
        wire.uuid = _get_uuid(items, 3, name)
        return wire


class SchematicBitmapV6(object):
    @staticmethod
    def parse(items):
        bmp = SchematicBitmapV6()
        if len(items) == 5:
            bmp.scale = _check_symbol_float(items, 2, 'image', 'scale')
            index = 3
        else:
            _check_len_total(items, 4, 'image')
            bmp.scale = None
            index = 2
        bmp.pos_x, bmp.pos_y, bmp.ang = _get_at(items, 1, 'image')
        bmp.uuid = _get_uuid(items, index, 'image')
        values = _check_symbol_value(items, index+1, 'image data', 'data')
        bmp.data = [_check_symbol(values, i+1, 'image data') for i, d in enumerate(values[1:])]
        return bmp


class PolyLine(object):
    @staticmethod
    def parse(items):
        _check_len_total(items, 4, 'polyline')
        poly = PolyLine()
        poly.points = _get_points(items[1])
        poly.stroke = Stroke.parse(items[2])
        poly.uuid = _get_uuid(items, 3, 'polyline')
        return poly


class Text(object):
    @staticmethod
    def parse(items, name):
        _check_len_total(items, 5, name)
        text = Text()
        text.name = name
        text.text = _check_str(items, 1, name)
        text.pos_x, text.pos_y, text.ang = _get_at(items, 2, name)
        text.effects = _get_effects(items, 3, name)
        text.uuid = _get_uuid(items, 4, name)
        return text


class GlobalLabel(object):
    def __init__(self):
        super().__init__()
        self.text = ''
        self.shape = None
        self.fields_autoplaced = False
        self.pos_x = self.pos_y = self.ang = 0
        self.effects = None
        self.uuid = None
        self.properties = []

    @staticmethod
    def parse(items):
        label = GlobalLabel()
        label.text = _check_str(items, 1, 'global_label')
        for c, i in enumerate(items[2:]):
            i_type = _check_is_symbol_list(i)
            if i_type == 'shape':
                label.shape = _check_symbol(i, 1, i_type)
            elif i_type == 'fields_autoplaced':
                label.fields_autoplaced = True
            elif i_type == 'at':
                label.pos_x, label.pos_y, label.ang = _get_at(items, c+2, 'global_label')
            elif i_type == 'effects':
                label.effects = FontEffects.parse(i)
            elif i_type == 'uuid':
                label.uuid = _get_uuid(items, c+2, 'global_label')
            elif i_type == 'property':
                label.properties.append(SchematicFieldV6.parse(i))
            else:
                raise SchError('Unknown label attribute `{}`'.format(i))
        return label


class HierarchicalLabel(object):
    @staticmethod
    def parse(items):
        name = 'hierarchical_label'
        _check_len_total(items, 6, name)
        label = HierarchicalLabel()
        label.text = _check_str(items, 1, name)
        label.shape = _check_symbol(items[2], 1, 'shape')
        label.pos_x, label.pos_y, label.ang = _get_at(items, 3, name)
        label.effects = _get_effects(items, 4, name)
        label.uuid = _get_uuid(items, 5, name)
        return label


class HSPin(object):
    """ Hierarchical Sheet Pin """
    @staticmethod
    def parse(items):
        name = 'hierarchical sheet pin'
        _check_len_total(items, 6, name)
        pin = HSPin()
        pin.name = _check_str(items, 1, name+' name')
        pin.type = _check_symbol(items, 2, name+' type')
        pin.pos_x, pin.pos_y, pin.ang = _get_at(items, 3, name)
        pin.effects = _get_effects(items, 4, name)
        pin.uuid = _get_uuid(items, 5, name)
        return pin


class Sheet(object):
    def __init__(self):
        super().__init__()
        self.pos_x = self.pos_y = self.ang = 0
        self.w = self.h = 0
        self.fields_autoplaced = False
        self.stroke = self.fill = self.uuid = None
        self.properties = []
        self.name = self.file = ''
        self.pins = []

    @staticmethod
    def parse(items):
        sheet = Sheet()
        for c, i in enumerate(items[1:]):
            i_type = _check_is_symbol_list(i)
            if i_type == 'at':
                sheet.pos_x, sheet.pos_y, sheet.ang = _get_at(items, c+1, 'sheet')
            elif i_type == 'size':
                sheet.w = _check_float(i, 1, 'sheet width')
                sheet.h = _check_float(i, 2, 'sheet height')
            elif i_type == 'fields_autoplaced':
                sheet.fields_autoplaced = True
            elif i_type == 'stroke':
                sheet.stroke = Stroke.parse(i)
            elif i_type == 'fill':
                sheet.fill = Fill.parse(i)
            elif i_type == 'uuid':
                sheet.uuid = _get_uuid(items, c+1, 'sheet')
            elif i_type == 'property':
                field = SchematicFieldV6.parse(i)
                sheet.properties.append(field)
                if field.name == 'Sheet name':
                    sheet.name = field.value
                elif field.name == 'Sheet file':
                    sheet.file = field.value
                else:
                    logger.warning(W_UNKFLD+"Unknown sheet property `{}` ({})".format(field.name, field.value))
            elif i_type == 'pin':
                sheet.pins.append(HSPin.parse(i))
            else:
                raise SchError('Unknown sheet attribute `{}`'.format(i))
        return sheet

    def load_sheet(self, project, parent_file, parent_obj):
        assert self.name
        sheet = SchematicV6()
        self.sheet = sheet
        parent_dir = os.path.dirname(parent_file)
        sheet.path = os.path.join(parent_obj.path, self.uuid)
        sheet.sheet_path_h = os.path.join(parent_obj.sheet_path_h, self.name)
        parent_obj.sheet_paths[sheet.path] = sheet
        sheet.load(os.path.join(parent_dir, self.file), project, parent_obj)
        return sheet


class SheetInstance(object):
    @staticmethod
    def parse(items):
        name = 'sheet instance'
        instances = []
        for c, i in enumerate(items[1:]):
            v = _check_symbol_value(items, c+1, name, 'path')
            instance = SheetInstance()
            instance.path = _check_str(v, 1, name+' path')
            instance.page = _check_symbol_str(v, 2, name, 'page')
            instances.append(instance)
        return instances


class SymbolInstance(object):
    @staticmethod
    def parse(items):
        name = 'symbol instance'
        instances = []
        for c, i in enumerate(items[1:]):
            v = _check_symbol_value(items, c+1, name, 'path')
            instance = SymbolInstance()
            instance.path = _check_str(v, 1, name+' path')
            instance.reference = _check_symbol_str(v, 2, name, 'reference')
            instance.unit = _check_symbol_int(v, 3, name, 'unit')
            instance.value = _check_symbol_str(v, 4, name, 'value')
            instance.footprint = _check_symbol_str(v, 5, name, 'footprint')
            instances.append(instance)
        return instances


class SchematicV6(Schematic):
    def __init__(self):
        super().__init__()
        self.annotation_error = False
        # The title block is optional
        self.date = self.title = self.revision = self.company = ''
        self.comment1 = self.comment2 = self.comment3 = self.comment4 = ''

    def _fill_missing_title_block(self):
        # Fill in some missing info
        self.date = GS.format_date(self.date, self.fname, 'SCH')
        if not self.title:
            self.title = os.path.splitext(os.path.basename(self.fname))[0]

    def _get_title_block(self, items):
        if not isinstance(items, list):
            raise SchError('The title block is not a list')
        for item in items:
            if not isinstance(item, list) or len(item) < 2 or not isinstance(item[0], Symbol):
                raise SchError('Wrong title block entry ({})'.format(item))
            i_type = item[0].value()
            if i_type == 'title':
                self.title = _check_str(item, 1, i_type)
            elif i_type == 'date':
                self.date = _check_str(item, 1, i_type)
            elif i_type == 'rev':
                self.revision = _check_str(item, 1, i_type)
            elif i_type == 'company':
                self.company = _check_str(item, 1, i_type)
            elif i_type == 'comment':
                index = _check_integer(item, 1, i_type)
                if index < 1 or index > 4:
                    raise SchError('Unsupported comment index {} in title block'.format(index))
                value = _check_str(item, 2, i_type)
                if index == 1:
                    self.comment1 = value
                elif index == 2:
                    self.comment2 = value
                elif index == 3:
                    self.comment3 = value
                elif index == 4:
                    self.comment4 = value
            else:
                raise SchError('Unsupported entry in title block ({})'.format(item))
        self._fill_missing_title_block()
        logger.debug("SCH title: `{}`".format(self.title))
        logger.debug("SCH date: `{}`".format(self.date))
        logger.debug("SCH revision: `{}`".format(self.revision))
        logger.debug("SCH company: `{}`".format(self.company))

    def _get_lib_symbols(self, comps):
        if not isinstance(comps, list):
            raise SchError('The lib symbols is not a list')
        for c in comps[1:]:
            obj = LibComponent.load(c, self.project)
            self.lib_symbols.append(obj)
            self.lib_symbol_names[obj.lib_id] = obj

    def load(self, fname, project, parent=None):  # noqa: C901
        """ Load a v6.x KiCad Schematic.
            The caller must be sure the file exists.
            Only the schematics are loaded not the libs. """
        logger.debug("Loading sheet from "+fname)
        if parent is None:
            self.fields = ['part']
            self.fields_lc = set(self.fields)
            self.sheet_paths = {'/': self}
            self.symbol_uuids = {}
            self.lib_symbol_names = {}
            self.path = '/'
            self.sheet_path_h = '/'
        else:
            self.fields = parent.fields
            self.fields_lc = parent.fields_lc
            self.sheet_paths = parent.sheet_paths
            self.symbol_uuids = parent.symbol_uuids
            self.lib_symbol_names = parent.lib_symbol_names
            # self.path is set by sch.load_sheet
        self.parent = parent
        self.fname = fname
        self.project = project
        self.all = []
        self.lib_symbols = []
        self.symbols = []
        self.components = []
        self.juntions = []  # Connect
        self.no_conn = []
        self.bus_entry = []
        self.wires = []
        self.bitmaps = []
        self.texts = []
        self.lines = []
        self.labels = []
        self.glabels = []
        self.hlabels = []
        self.sheets = []
        self.sheet_instances = []
        self.symbol_instances = []
        with open(fname, 'rt') as fh:
            error = None
            try:
                sch = load(fh)
            except SExpData as e:
                error = str(e)
            if error:
                raise SchError(error)
        if sch[0].value() != 'kicad_sch':
            raise SchError('No kicad_sch signature')
        for e in sch[1:]:
            e_type = _check_is_symbol_list(e)
            obj = None
            if e_type == 'version':
                self.version = _check_integer(e, 1, e_type)
            elif e_type == 'generator':
                self.generator = _check_symbol(e, 1, e_type)
            elif e_type == 'uuid':
                self.uuid = _check_symbol(e, 1, e_type)
            elif e_type == 'paper':
                self.paper = _check_str(e, 1, e_type)
                index = 2
                if self.paper == "User":
                    self.paper_w = _check_float(e, 2, 'paper width')
                    self.paper_h = _check_float(e, 3, 'paper height')
                    index += 2
                if len(e) > index:
                    self.paper_orientation = _check_symbol(e, index, 'paper orientation')
                else:
                    self.paper_orientation = None
            elif e_type == 'title_block':
                self._get_title_block(e[1:])
            elif e_type == 'lib_symbols':
                self._get_lib_symbols(e)
            # The following are mixed
            elif e_type == 'junction':
                obj = Junction.parse(e)
                self.juntions.append(obj)
            elif e_type == 'no_connect':
                obj = NoConnect.parse(e)
                self.no_conn.append(obj)
            elif e_type == 'bus_entry':
                obj = BusEntry.parse(e)
                self.bus_entry.append(obj)
            elif e_type == 'bus' or e_type == 'wire':
                obj = SchematicWireV6.parse(e, e_type)
                self.wires.append(obj)
            elif e_type == 'image':
                obj = SchematicBitmapV6.parse(e)
                self.bitmaps.append(obj)
            elif e_type == 'polyline':
                obj = PolyLine.parse(e)
                self.lines.append(obj)
            elif e_type == 'text':
                obj = Text.parse(e, e_type)
                self.texts.append(obj)
            elif e_type == 'label':
                obj = Text.parse(e, e_type)
                self.labels.append(obj)
            elif e_type == 'global_label':
                obj = GlobalLabel.parse(e)
                self.glabels.append(obj)
            elif e_type == 'hierarchical_label':
                obj = HierarchicalLabel.parse(e)
                self.hlabels.append(obj)
            # Ordered again
            elif e_type == 'symbol':
                obj = SchematicComponentV6.load(e, self.project, self)
                if obj.annotation_error:
                    self.annotation_error = True
                self.symbols.append(obj)
                self.symbol_uuids[obj.uuid] = obj
            elif e_type == 'sheet':
                obj = Sheet.parse(e)
                self.sheets.append(obj)
            elif e_type == 'sheet_instances':
                self.sheet_instances = SheetInstance.parse(e)
            elif e_type == 'symbol_instances':
                self.symbol_instances = SymbolInstance.parse(e)
            else:
                raise SchError('Unknown kicad_sch attribute `{}`'.format(e))
            if obj is not None:
                self.all.append(obj)
        if not self.title:
            self._fill_missing_title_block()
        # Load sub-sheets
        self.sub_sheets = []
        for sch in self.sheets:
            sheet = sch.load_sheet(project, fname, self)
            if sheet.annotation_error:
                self.annotation_error = True
            self.sub_sheets.append(sheet)
        # Create the components list
        for s in self.symbol_instances:
            # Get a copy of the original symbol
            path = os.path.dirname(s.path)
            sheet = self.sheet_paths[path]
            comp_uuid = os.path.basename(s.path)
            comp = deepcopy(self.symbol_uuids[comp_uuid])
            # Transfer the instance data
            comp.set_ref(s.reference)
            comp.unit = s.unit
            comp.value = s.value
            comp.set_footprint(s.footprint)
            # Link with its library symbol
            try:
                lib_symbol = self.lib_symbol_names[comp.lib_id]
            except KeyError:
                logger.warning(W_MISSCMP+'Missing component `{}`'.format(comp.lib_id))
                lib_symbol = LibComponent()
            comp.lib_symbol = lib_symbol
            comp.is_power = lib_symbol.is_power
            # Add it to the list
            self.components.append(comp)
