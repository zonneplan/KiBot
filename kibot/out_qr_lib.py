# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from qrcodegen import QrCode
from .gs import GS
if GS.ki6():  # pragma: no cover (Ki6)
    from pcbnew import IU_PER_MM, S_POLYGON, wxPoint, ADD_MODE_APPEND
    ADD_APPEND = ADD_MODE_APPEND
else:
    from pcbnew import IU_PER_MM, S_POLYGON, wxPoint, ADD_APPEND
from .optionable import BaseOptions, Optionable
from .out_base import VariantOptions
from .error import KiPlotConfigurationError
from .kicad.sexpdata import Symbol, dumps, Sep, load, SExpData
from .kicad.v6_sch import DrawRectangleV6, PointXY, Stroke, Fill, SchematicFieldV6, FontEffects
from .macros import macros, document, output_class  # noqa: F401
from . import log

QR_ECCS = {'low': QrCode.Ecc.LOW,
           'medium': QrCode.Ecc.MEDIUM,
           'quartile': QrCode.Ecc.QUARTILE,
           'high': QrCode.Ecc.HIGH}
logger = log.get_logger()


class QRCodeOptions(Optionable):
    """ A QR code """
    def __init__(self, field=None):
        super().__init__()
        with document:
            self.name = 'QR'
            """ Name for the symbol/footprint """
            self.text = '%p %r'
            """ Text to encode as QR """
            self.correction_level = 'low'
            """ [low,medium,quartile,high] Error correction level """
            self.size_sch = 15
            """ Size of the QR symbol """
            self.size_pcb = 15
            """ Size of the QR footprint """
            self.size_units = 'millimeters'
            """ [millimeters,inches] Units used for the size """
            self.layer = 'silk'
            """ [silk,copper] Layer for the footprint """
            self.pcb_negative = False
            """ Generate a negative image for the PCB """
        self._unkown_is_error = True
        self._update_mode = False

    def config(self, parent):
        super().config(parent)
        self.correction_level = QR_ECCS[self.correction_level]
        self.layer = 'F.SilkS' if self.layer == 'silk' else 'F.Cu'


class QR_LibOptions(BaseOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ Filename for the output (%i=qr, %x=lib) """
            self.lib = 'QR'
            """ Short name for the library """
            self.reference = 'QR'
            """ The reference prefix """
            self.use_sch_dir = True
            """ Generate the libs relative to the schematic/PCB dir """
            self.qrs = QRCodeOptions
            """ [list(dict)] QR codes to include in the library """
        super().__init__()
        self._expand_id = 'qr'
        self._expand_ext = 'lib'

    def config(self, parent):
        super().config(parent)
        if isinstance(self.qrs, type):
            raise KiPlotConfigurationError("You must specify at least one QR code")
        names = set()
        for qr in self.qrs:
            if qr.name in names:
                raise KiPlotConfigurationError("QR code name `{}` repeated".format(qr.name))
            names.add(qr.name)

    def symbol_k5(self, f, qr):
        # Compute the size
        qrc = qr._code_sch
        size = qrc.get_size()
        full_size = qr.size_sch * (39.37007874 if qr.size_units == 'millimeters' else 1000)
        center = round(full_size/2)
        size_rect = full_size/size
        # Generate the symbol
        f.write("#\n# {}\n#\n".format(qr.name))
        f.write("DEF {} {} 0 {} N N 1 F N\n".format(qr.name, '#'+self.reference, 0))
        # Reference
        f.write('F0 "{}" {} {} 50 H I L BNN\n'.format('#'+self.reference, -center, center+60))
        # Value
        f.write('F1 "{}" {} {} 50 H I L TNN\n'.format(qr.name, -center, -center))
        # Footprint
        f.write('F2 "{}:{}" 0 150 50 H I C CNN\n'.format(self.lib, qr.name))
        # Datasheet
        f.write('F3 "" 0 0 50 H I C CNN\n')
        # QR information
        f.write('F4 "{}" 0 0 50 H I C CNN "qr_version"\n'.format(qrc.get_version()))
        f.write('F5 "{}" 0 0 50 H I C CNN "qr_size"\n'.format(size))
        ecc = qrc.get_error_correction_level()
        f.write('F6 "{},{}" 0 0 50 H I C CNN "qr_ecc"\n'.format(ecc.ordinal, ecc.formatbits))
        f.write('F7 "{}" 0 0 50 H I C CNN "qr_mask"\n'.format(qrc.get_mask()))
        f.write('F8 "{}" 0 0 50 H I C CNN "qr_text"\n'.format(qr._text_sch.replace('"', '\"')))
        f.write("DRAW\n")
        for y in range(size):
            for x in range(size):
                if qrc.get_module(x, y):
                    x_pos = round(x*size_rect-center)
                    y_pos = round(center-y*size_rect)
                    f.write('S {} {} {} {} 0 0 1 F\n'.format(x_pos, y_pos, round(x_pos+size_rect), round(y_pos+size_rect)))
        f.write("ENDDRAW\n")
        f.write("ENDDEF\n")

    def fp_field(self, center, name, value, layer, id):
        if id == 0:
            pos_y = center+1.25
        else:
            pos_y = -(center+1.25+1.7*(id-1))
        fld = [Symbol('fp_text'), Symbol(name), value]
        fld.append([Symbol('at'), 0, pos_y])
        fld.append([Symbol('layer'), Symbol(layer)])
        if name == 'user':
            fld.append(Symbol('hide'))
        fld.append(Sep())
        font = [Symbol('font')]
        font.append([Symbol('size'), 1, 1])
        font.append([Symbol('thickness'), 0.15])
        fld.append([Symbol('effects'), font])
        fld.append(Sep())
        return fld

    def qr_draw_fp(self, size, size_rect, center, qrc, negative, layer):
        mod = []
        for y in range(size):
            for x in range(size):
                if qrc.get_module(x-negative, y-negative) ^ negative:
                    x_pos = round(x*size_rect-center, 2)
                    y_pos = round(y*size_rect-center, 2)
                    x_pos2 = round(x_pos+size_rect, 2)
                    y_pos2 = round(y_pos+size_rect, 2)
                    rect = [Symbol('fp_poly')]  # fp_rect not in v5
                    pts = [Symbol('pts')]
                    pts.append([Symbol('xy'), x_pos, y_pos])
                    pts.append([Symbol('xy'), x_pos, y_pos2])
                    pts.append([Symbol('xy'), x_pos2, y_pos2])
                    pts.append([Symbol('xy'), x_pos2, y_pos])
                    rect.append(pts)
                    if layer:
                        rect.append([Symbol('layer'), Symbol(layer)])
                    rect.append([Symbol('width'), 0])
                    mod.append(rect)
                    mod.append(Sep())
        return mod

    def qr_draw_fp_memory(self, m, size, size_rect, center, qrc, negative, layer):
        """ Create the QR drawings for the board in memory """
        for y in range(size):
            for x in range(size):
                if qrc.get_module(x-negative, y-negative) ^ negative:
                    x_pos = round(x*size_rect-center, 2)
                    y_pos = round(y*size_rect-center, 2)
                    x_pos2 = round(x_pos+size_rect, 2)
                    y_pos2 = round(y_pos+size_rect, 2)
                    # Convert to Internal Units
                    x_pos *= IU_PER_MM
                    y_pos *= IU_PER_MM
                    x_pos2 *= IU_PER_MM
                    y_pos2 *= IU_PER_MM
                    # Create a PCB polygon
                    poly = VariantOptions.create_module_element(m)
                    poly.SetShape(S_POLYGON)
                    points = []
                    points.append(wxPoint(x_pos, y_pos))
                    points.append(wxPoint(x_pos, y_pos2))
                    points.append(wxPoint(x_pos2, y_pos2))
                    points.append(wxPoint(x_pos2, y_pos))
                    poly.SetPolyPoints(points)
                    poly.SetLayer(layer)
                    poly.SetWidth(0)
                    poly.thisown = 0
                    m.AddNative(poly, ADD_APPEND)

    def qr_draw_sym(self, size, size_rect, center, qrc):
        mod = []
        for y in range(size):
            for x in range(size):
                if qrc.get_module(x, y):
                    x_pos = round(x*size_rect-center, 2)
                    y_pos = round(center-y*size_rect, 2)
                    rect = DrawRectangleV6()
                    rect.start = PointXY(x_pos, y_pos)
                    rect.end = PointXY(round(x_pos+size_rect, 2), round(y_pos-size_rect, 2))
                    rect.stroke = Stroke()
                    rect.stroke.width = 0.001
                    rect.fill = Fill()
                    rect.fill.type = 'outline'
                    mod.append(rect.write())
                    mod.append(Sep())
        return mod

    def footprint(self, dir, qr):
        # Compute the size
        qrc = qr._code_pcb
        size = qrc.get_size()
        if qr.pcb_negative:
            size += 2
        full_size = qr.size_pcb * (1 if qr.size_units == 'millimeters' else 25.4)
        center = round(full_size/2, 2)
        size_rect = round(full_size/size, 2)
        # Generate the footprint
        fname = os.path.join(dir, qr.name+'.kicad_mod')
        mod = [Symbol('module'), Symbol(qr.name)]
        mod.append([Symbol('layer'), Symbol(qr.layer)])
        mod.append([Symbol('tedit'), 0])
        mod.append(Sep())
        mod.append(self.fp_field(center, 'reference', self.reference+'***', qr.layer, 0))
        mod.append(Sep())
        mod.append(self.fp_field(center, 'value', qr.name, qr.layer, 1))
        mod.append(Sep())
        mod.append(self.fp_field(center, 'user', 'qr_version: '+str(qrc.get_version()), qr.layer, 2))
        mod.append(Sep())
        mod.append(self.fp_field(center, 'user', 'qr_size: '+str(size), qr.layer, 3))
        mod.append(Sep())
        ecc = qrc.get_error_correction_level()
        mod.append(self.fp_field(center, 'user', 'qr_ecc: {},{}'.format(ecc.ordinal, ecc.formatbits), qr.layer, 4))
        mod.append(Sep())
        mod.append(self.fp_field(center, 'user', 'qr_mask: '+str(qrc.get_mask()), qr.layer, 5))
        mod.append(Sep())
        mod.append(self.fp_field(center, 'user', qr._text_sch, qr.layer, 6))
        mod.append(Sep())
        # The QR itself
        mod.extend(self.qr_draw_fp(size, size_rect, center, qrc, qr.pcb_negative, qr.layer))
        with open(fname, 'wt') as f:
            f.write(dumps(mod))
            f.write('\n')

    def symbol_lib_k5(self):
        self._expand_ext = 'lib'
        output = os.path.join(self._odir_sch, self.expand_filename_sch(self.output))
        logger.debug('Creating KiCad 5 symbols library: '+output)
        with open(output, 'wt') as f:
            f.write("EESchema-LIBRARY Version 2.4\n")
            f.write("#encoding utf-8\n")
            for qr in self.qrs:
                logger.debug('Adding symbol: '+qr.name)
                self.symbol_k5(f, qr)
            f.write("#\n#End Library\n")

    def sym_field(self, center, name, value, id):
        if id == 0:
            pos_y = center+1.25
        else:
            pos_y = -(center+1.25+1.7*(id-1))
        f = SchematicFieldV6(name, str(value), id, 0, round(pos_y, 2))
        if id > 1:
            f.effects = FontEffects()
            f.effects.hide = True
        return f.write()+[Sep()]

    def symbol_lib_k6(self):
        self._expand_ext = 'kicad_sym'
        output = os.path.join(self._odir_sch, self.expand_filename_sch(self.output))
        logger.debug('Creating KiCad 6 symbols library: '+output)
        # Lib header
        lib = [Symbol('kicad_symbol_lib')]
        lib.append([Symbol('version'), 20211014])
        lib.append([Symbol('generator'), Symbol('kibot')])
        lib.append(Sep())
        for qr in self.qrs:
            logger.debug('Adding symbol: '+qr.name)
            # Compute the size
            qrc = qr._code_sch
            size = qrc.get_size()
            full_size = qr.size_sch * (1 if qr.size_units == 'millimeters' else 25.4)
            center = round(full_size/2, 2)
            size_rect = round(full_size/size, 2)
            # Symbol main attributes
            sym = [Symbol('symbol'), qr.name]
            sym.append([Symbol('pin_numbers'), Symbol('hide')])
            sym.append([Symbol('pin_names'), Symbol('hide')])
            sym.append([Symbol('in_bom'), Symbol('no')])
            sym.append([Symbol('on_board'), Symbol('yes')])
            sym.append(Sep())
            # Properties (Fields)
            sym.append(self.sym_field(center, 'Reference', '#'+self.reference, 0))
            sym.append(Sep())
            sym.append(self.sym_field(center, 'Value', qr.name, 1))
            sym.append(Sep())
            sym.append(self.sym_field(center, 'Footprint', self.lib+':'+qr.name, 2))
            sym.append(Sep())
            sym.append(self.sym_field(center, 'Datasheet', '', 3))
            sym.append(Sep())
            sym.append(self.sym_field(center, 'qr_version', qrc.get_version(), 4))
            sym.append(Sep())
            sym.append(self.sym_field(center, 'qr_size', size, 5))
            sym.append(Sep())
            ecc = qrc.get_error_correction_level()
            sym.append(self.sym_field(center, 'qr_ecc', '{},{}'.format(ecc.ordinal, ecc.formatbits), 6))
            sym.append(Sep())
            sym.append(self.sym_field(center, 'qr_mask', qrc.get_mask(), 7))
            sym.append(Sep())
            sym.append(self.sym_field(center, 'qr_text', qr._text_sch, 8))
            sym.append(Sep())
            sym.extend(self.qr_draw_sym(size, size_rect, center, qrc))
            lib.append(sym)
            lib.append(Sep())
        with open(output, 'wt') as f:
            f.write(dumps(lib))
            f.write('\n')

    def update_footprint(self, name, qr):
        logger.debug('Updating QR footprint: '+name)
        # Compute the size
        # TODO: don't repeat
        qrc = qr._code_pcb
        size = qrc.get_size()
        if qr.pcb_negative:
            size += 2
        full_size = qr.size_pcb * (1 if qr.size_units == 'millimeters' else 25.4)
        center = round(full_size/2, 2)
        size_rect = round(full_size/size, 2)
        # Replace any instance
        name = name.lower()
        for m in GS.get_modules():
            id = m.GetFPID()
            m_name = ('{}:{}'.format(id.GetLibNickname(), id.GetLibItemName())).lower()
            if name == m_name:
                ref = m.GetReference()
                logger.debug('- Updating '+ref)
                # Remove all the drawings
                for gi in m.GraphicalItems():
                    if gi.GetClass() == 'MGRAPHIC':
                        m.Remove(gi)
                # Add the updated version
                self.qr_draw_fp_memory(m, size, size_rect, center, qrc, qr.pcb_negative, GS.board.GetLayerID(qr.layer))

    def load_k6_sheet(self, fname):
        with open(fname, 'rt') as fh:
            error = None
            try:
                sch = load(fh)
            except SExpData as e:
                error = str(e)
            if error:
                raise KiPlotConfigurationError(error)
        return sch

    def load_k6_sheets(self, fname, sheets={}):
        assert GS.sch_file is not None
        sheet = self.load_k6_sheet(fname)
        sheets[fname] = sheet
        if not isinstance(sheet, list) or sheet[0].value() != 'kicad_sch':
            raise KiPlotConfigurationError('No kicad_sch signature in '+fname)
        for e in sheet[1:]:
            if isinstance(e, list) and isinstance(e[0], Symbol) and e[0].value == 'sheet':
                logger.error(e)

    def run(self, output):
        if self.use_sch_dir:
            self._odir_sch = GS.sch_dir
            self._odir_pcb = GS.pcb_dir
        else:
            self._odir_pcb = self._odir_sch = self._parent.output_dir
        # Create the QR codes
        for qr in self.qrs:
            qr._text_sch = self.expand_filename_both(qr.text, make_safe=False)
            qr._code_sch = QrCode.encode_text(qr._text_sch, qr.correction_level)
            qr._text_pcb = self.expand_filename_both(qr.text, is_sch=False, make_safe=False)
            qr._code_pcb = QrCode.encode_text(qr._text_pcb, qr.correction_level)
        # Create the symbols
        if GS.ki5():
            self.symbol_lib_k5()
        else:
            self.symbol_lib_k6()
        # Create the footprints
        self._expand_ext = 'pretty'
        dir_pretty = os.path.join(self._odir_pcb, self.expand_filename_pcb(self.output))
        logger.debug('Creating footprints library: '+dir_pretty)
        os.makedirs(dir_pretty, exist_ok=True)
        for qr in self.qrs:
            logger.debug('Adding footprint: '+qr.name)
            self.footprint(dir_pretty, qr)
        # Update the files
        if self._parent._update_mode:
            # PCB
            assert GS.board is not None
            for qr in self.qrs:
                self.update_footprint(self.lib+':'+qr.name, qr)
            bkp = GS.pcb_file+'-bak'
            if os.path.isfile(bkp):
                os.remove(bkp)
            os.rename(GS.pcb_file, bkp)
            GS.board.Save(GS.pcb_file)
            # Schematic
            if GS.ki6():
                # KiCad 5 reads the lib, but KiCad 6 is more like the PCB
                # sheets = self.load_k6_sheets(GS.sch_file)
                pass
                # TODO: KiCad 6 is crashing when we delete the graphics


@output_class
class QR_Lib(BaseOutput):  # noqa: F821
    """ QR_Lib
        Generates a QR code symbol and footprint.
        This output creates a library containing a symbol and footprint for a QR code. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = QR_LibOptions
            """ [dict] Options for the `boardview` output """
        self._both_related = True
