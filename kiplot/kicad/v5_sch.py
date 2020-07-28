"""
KiCad v5 (and older) Schematic format.

A basic implementation of the .sch file format.
"""
import re
import os
from ..gs import GS
from .. import log

logger = log.get_logger(__name__)

_sch_line_number = 0


class SchError(Exception):
    pass


class SchFileError(SchError):
    pass


def _get_line(f):
    res = f.readline()
    if not res:
        raise SchFileError('Unexpected end of file')
    global _sch_line_number
    _sch_line_number += 1
    return res.rstrip()


def _split_space(s):
    res = s.lstrip().split(' ')
    return [a for a in res if a]


class SchematicField(object):
    field_re = re.compile(r'F\s+(\d+)\s+"([^"]*)"\s+([HV])\s+(-?\d+)\s+(-?\d+)\s+(\d+)\s+(\d+)'
                          r'\s+([LRCBT])\s+([LRCBT][IN][BN])\s*("[^"]*")?')

    def __init__(self):
        super().__init__()

    @staticmethod
    def parse(line):
        m = SchematicField.field_re.match(line)
        if not m:
            raise SchFileError('Malformed component field', line, _sch_line_number)
        field = SchematicField()
        gs = m.groups()
        field.number = int(gs[0])
        field.value = gs[1]
        field.horizontal = gs[2] == 'H'  # H -> True, V -> False
        field.x = int(gs[3])
        field.y = int(gs[4])
        field.size = int(gs[5])
        field.flags = gs[6]
        field.hjustify = gs[7]
        field.vjustify = gs[8][0]
        field.italic = gs[8][1] == 'I'
        field.bold = gs[8][2] == 'B'
        if gs[9]:
            field.name = gs[9][1:-1]
        else:
            if field.number > 4:
                raise SchFileError('Missing component field name', line, _sch_line_number)
            field.name = ['Reference', 'Value', 'Footprint', 'Datasheet'][field.number]
        return field


class SchematicAltRef():
    def __init__(self):
        super().__init__()
        self.path = None
        self.ref = None
        self.part = None

    @staticmethod
    def parse(line):
        ar = SchematicAltRef()
        res = _split_space(line[3:])
        for r in res:
            if r.startswith('Path='):
                ar.path = r[6:-1]
            elif r.startswith('Ref='):
                ar.ref = r[5:-1]
            elif r.startswith('Part='):
                ar.part = r[6:-1]
            else:
                logger.warning('Unknown AR field `{}`'.format(r))
        if not ar.path:
            logger.warning('Alternative Reference without path `{}`'.format(line))
        if not ar.ref:
            logger.warning('Alternative Reference without reference `{}`'.format(line))
        return ar


class SchematicComponent(object):
    ref_re = re.compile(r'([^\d]+)([\?\d]+)')

    def __init__(self):
        super().__init__()
        self.field_ref = ''
        self.value = ''
        self.footprint = ''
        self.datasheet = ''

    def get_field_value(self, field):
        field = field.lower()
        if field in self.dfields:
            return self.dfields[field].value
        return ''

    def get_field_names(self):
        return [f.name for f in self.fields]

    def add_field(self, field):
        self.fields.append(field)
        self.dfields[field.name.lower()] = field

    def _solve_ref(self, path):
        """ Look fo the correct reference for this path.
            Returns the default reference if no paths defined.
            Returns the first not empty reference if the current is empty. """
        ref = self.f_ref
        # If the reference is empty try the reference field
        if ref[-1] == '?' and self.field_ref and self.field_ref[-1] != '?':
            ref = self.fields[0].value
        if self.ar:
            path += '/'+self.id
            for o in self.ar:
                if o.path == path and o.ref[-1] != '?':
                    return o.ref
                if ref[-1] == '?' and o.ref[-1] != '?':
                    ref = o.ref
        return ref

    def _solve_fields(self):
        """ Fills the default fields from the fields attribute """
        f = self.fields
        c = len(f)
        self.field_ref = None
        self.value = None
        self.footprint = None
        self.footprint_lib = None
        self.datasheet = None
        if len(f) < 4:
            logger.warning('Component {} without the basic fields'.format(self.ref))
        if c > 0:
            self.field_ref = f[0].value
        if c > 1:
            self.value = f[1].value
        if c > 2:
            res = f[2].value.split(':')
            cres = len(res)
            if cres == 1:
                self.footprint = res[0]
            elif cres == 2:
                self.footprint_lib = res[0]
                self.footprint = res[1]
            else:
                raise SchFileError('Footprint with more than one colon', f[2].value, _sch_line_number)
        if c > 3:
            self.datasheet = f[3].value

    def __str__(self):
        if self.name == self.value:
            return '{} ({})'.format(self.ref, self.name, self.value)
        return '{} ({} {})'.format(self.ref, self.name, self.value)

    @staticmethod
    def load(f, sheet_path):
        # L lib:name reference
        line = _get_line(f)
        if line[0] != 'L':
            raise SchFileError('Missing component label', line, _sch_line_number)
        res = _split_space(line[2:])
        if len(res) != 2:
            raise SchFileError('Malformed component label', line, _sch_line_number)
        comp = SchematicComponent()
        comp.name, comp.f_ref = res
        res = comp.name.split(':')
        comp.lib = None
        if len(res) == 2:
            comp.name = res[1]
            comp.lib = res[0]
        # U N mm time_stamp
        line = _get_line(f)
        if line[0] != 'U':
            raise SchFileError('Missing component unit', line, _sch_line_number)
        res = _split_space(line[2:])
        if len(res) != 3:
            raise SchFileError('Malformed component unit', line, _sch_line_number)
        comp.unit = int(res[0])
        comp.unit2 = int(res[1])
        comp.id = res[2]
        # P x y
        line = _get_line(f)
        if line[0] != 'P':
            raise SchFileError('Missing component position', line, _sch_line_number)
        res = _split_space(line[2:])
        if len(res) != 2:
            raise SchFileError('Malformed component position', line, _sch_line_number)
        comp.x = int(res[0])
        comp.y = int(res[1])
        # Optional "Alternative References"
        line = _get_line(f)
        comp.ar = []
        while line[:2] == 'AR':
            comp.ar.append(SchematicAltRef.parse(line))
            line = _get_line(f)
        # F field_number "text" orientation posX posY size Flags (see below) hjustify vjustify/italic/bold "name"
        comp.fields = []
        comp.dfields = {}
        while line[0] == 'F':
            comp.add_field(SchematicField.parse(line))
            line = _get_line(f)
        # Redundant pos
        if not line.startswith('\t'+str(comp.unit)):
            raise SchFileError('Missing component redundant position', line, _sch_line_number)
        res = _split_space(line[2:])
        if len(res) != 2:
            raise SchFileError('Malformed component redundant position', line, _sch_line_number)
        xr = int(res[0])
        yr = int(res[1])
        if comp.x != xr or comp.y != yr:
            logger.warning('Inconsistent position for component {} ({},{} vs {},{})'.
                           format(comp.f_ref, comp.x, comp.y, xr, yr), line, _sch_line_number)
        # Orientation matrix
        line = _get_line(f)
        if line[0] != '\t':
            raise SchFileError('Missing component orientation matrix', line, _sch_line_number)
        res = _split_space(line[1:])
        if len(res) != 4:
            raise SchFileError('Malformed component orientation matrix', line, _sch_line_number)
        comp.matrix = [int(v) for v in res]
        line = _get_line(f)
        while not line.startswith('$EndComp'):
            line = _get_line(f)
        comp._solve_fields()
        comp.ref = comp._solve_ref(sheet_path)
        # Power, ground or power flag
        comp.is_power = comp.ref.startswith('#PWR') or comp.ref.startswith('#FLG')
        if comp.ref[-1] == '?':
            logger.warning('Component {} is not annotated'.format(comp))
        # Separate the reference in its components
        m = SchematicComponent.ref_re.match(comp.ref)
        if not m:
            raise SchFileError('Malformed component reference', comp.ref, _sch_line_number)
        comp.ref_prefix, comp.ref_suffix = m.groups()
        if GS.debug_level > 1:
            logger.debug("- Loaded component {}".format(comp))
        return comp


class SchematicConnection(object):
    conn_re = re.compile(r'\s*~\s+(-?\d+)\s+(-?\d+)')

    def __init__(self):
        super().__init__()

    @staticmethod
    def parse(connect, line):
        m = SchematicConnection.conn_re.match(line)
        if not m:
            raise SchFileError('Malformed no/connection', line, _sch_line_number)
        c = SchematicConnection()
        c.connect = connect
        c.x = int(m.group(1))
        c.y = int(m.group(2))
        return c


class SchematicText(object):
    label_re = re.compile(r'Text\s+(Notes|HLabel|GLabel|Label)\s+(-?\d+)\s+(-?\d+)\s+(\d)\s+(\d+)\s+(\S+)')

    def __init__(self):
        super().__init__()

    @staticmethod
    def load(f, line):
        m = SchematicText.label_re.match(line)
        if not m:
            raise SchFileError('Malformed text', line, _sch_line_number)
        text = SchematicText()
        gs = m.groups()
        text.type = gs[0]
        text.x = int(gs[1])
        text.y = int(gs[2])
        text.orient = int(gs[3])
        text.size = int(gs[4])
        text.shape = gs[5]
        text.text = _get_line(f)
        return text


class SchematicWire(object):
    WIRE = 0
    WIRE_BUS = 1
    WIRE_DOT = 2
    WIRES = {'Wire': WIRE, 'Bus': WIRE_BUS, 'Notes': WIRE_DOT}
    ENTRY_WIRE = 3
    ENTRY_BUS = 4
    ENTRIES = {'Wire': ENTRY_WIRE, 'Bus': ENTRY_BUS}

    def __init__(self):
        super().__init__()

    @staticmethod
    def load(f, line):
        res = _split_space(line)
        if len(res) != 3:
            raise SchFileError('Malformed wire', line, _sch_line_number)
        wire = SchematicText()
        if res[0] == 'Wire':
            if res[2] != 'Line' or res[1] not in SchematicWire.WIRES:
                raise SchFileError('Malformed wire', line, _sch_line_number)
            wire.type = SchematicWire.WIRES[res[1]]
        else:  # Entry
            if res[2] != 'Bus' or res[1] not in SchematicWire.ENTRIES:
                raise SchFileError('Malformed entry', line, _sch_line_number)
            wire.type = SchematicWire.ENTRIES[res[1]]
        line = _get_line(f)
        if line[0] != '\t':
            raise SchFileError('Malformed wire', line, _sch_line_number)
        res = _split_space(line[1:])
        if len(res) != 4:
            raise SchFileError('Malformed wire', line, _sch_line_number)
        wire.x = int(res[0])
        wire.y = int(res[1])
        wire.ex = int(res[2])
        wire.ey = int(res[3])
        return wire


class SchematicBitmap(object):
    def __init__(self):
        super().__init__()

    @staticmethod
    def load(f):
        # Position
        line = _get_line(f)
        res = _split_space(line.split)
        if len(res) != 3:
            raise SchFileError('Malformed bitmap position', line, _sch_line_number)
        if res[0] != 'Pos':
            raise SchFileError('Missing bitmap position', line, _sch_line_number)
        bmp = SchematicBitmap()
        bmp.x = int(res[1])
        bmp.y = int(res[2])
        # Scale
        line = _get_line(f)
        res = _split_space(line)
        if len(res) != 2:
            raise SchFileError('Malformed bitmap scale', line, _sch_line_number)
        if res[0] != 'Scale':
            raise SchFileError('Missing bitmap scale', line, _sch_line_number)
        bmp.scale = float(res[1].replace(',', '.'))
        # Data
        line = _get_line(f)
        if line != 'Data':
            raise SchFileError('Missing bitmap data', line, _sch_line_number)
        line = _get_line(f)
        bmp.data = b''
        while line != 'EndData':
            res = _split_space(line)
            bmp.data += bytes([int(b, 16) for b in res])
            line = _get_line(f)
        # End of bitmap
        line = _get_line(f)
        if line != '$EndBitmap':
            raise SchFileError('Missing end of bitmap', line, _sch_line_number)
        return bmp


class SchematicPort(object):
    port_re = re.compile(r'(\d+)\s+"(.*?)"\s+([IOBTU])\s+([RLTB])\s+(-?\d+)\s+(-?\d+)\s+(\d+)$')

    def __init__(self):
        super().__init__()

    @staticmethod
    def parse(line):
        m = SchematicPort.port_re.match(line)
        if not m:
            raise SchFileError('Malformed sheet port label', line, _sch_line_number)
        port = SchematicPort()
        res = m.groups()
        port.number = int(res[0])
        port.name = res[1]
        port.form = res[2]
        port.side = res[3]
        port.x = int(res[4])
        port.y = int(res[5])
        port.size = int(res[6])
        return port


class SchematicSheet(object):
    name_re = re.compile(r'"(.*?)"\s+(\d+)$')

    def __init__(self):
        super().__init__()
        self.sheet = None
        self.id = ''

    def load_sheet(self, parent, sheet_path):
        assert self.name
        self.sheet = Schematic()
        parent_dir = os.path.dirname(parent)
        sheet_path += '/'+self.id
        self.sheet.load(os.path.join(parent_dir, self.file), sheet_path)
        return self.sheet

    @staticmethod
    def load(f):
        # Position & Size
        line = _get_line(f)
        if line[0] != 'S':
            raise SchFileError('Missing sheet size and position', line, _sch_line_number)
        res = _split_space(line[2:])
        if len(res) != 4:
            raise SchFileError('Malformed sheet size and position', line, _sch_line_number)
        sch = SchematicSheet()
        sch.x = int(res[0])
        sch.y = int(res[1])
        sch.w = int(res[2])
        sch.h = int(res[3])
        # Optional U
        line = _get_line(f)
        if line[0] == 'U':
            sch.id = line[2:]
            line = _get_line(f)
        # Labels
        sch.labels = []
        sch.name = None
        sch.file = None
        while not line.startswith('$EndSheet'):
            if line[0] != 'F':
                raise SchFileError('Malformed sheet label', line, _sch_line_number)
            if line[1] == '0':
                m = SchematicSheet.name_re.match(line[2:].lstrip())
                if not m:
                    raise SchFileError('Malformed sheet name', line, _sch_line_number)
                sch.name = m.group(1)
                sch.name_size = int(m.group(2))
            elif line[1] == '1' and line[2] == ' ':
                m = SchematicSheet.name_re.match(line[2:].lstrip())
                if not m:
                    raise SchFileError('Malformed sheet file name', line, _sch_line_number)
                sch.file = m.group(1)
                sch.file_size = int(m.group(2))
            else:
                sch.labels.append(SchematicPort.parse(line[1:]))
            line = _get_line(f)
        if not sch.name:
            raise SchFileError('Missing sub-sheet name')
        if not sch.file:
            raise SchFileError('Missing sub-sheet file name', sch.name)
        return sch


class Schematic(object):
    def __init__(self):
        super().__init__()

    def _get_title_block(self, f):
        line = _get_line(f)
        m = re.match(r'\$Descr (\S+) (\d+) (\d+)', line)
        if not m:
            raise SchFileError('Missing $Descr', line, _sch_line_number)
        self.page_type = m.group(1)
        self.page_width = m.group(2)
        self.page_height = m.group(3)
        self.sheet = 1
        self.sheets = 1
        self.title_block = {}
        while True:
            line = _get_line(f)
            if line.startswith('$EndDescr'):
                return
            elif line.startswith('encoding'):
                if line[9:14] != 'utf-8':
                    raise SchFileError('Unsupported encoding', line, _sch_line_number)
            elif line.startswith('Sheet'):
                res = _split_space(line[6:])
                if len(res) != 2:
                    raise SchFileError('Wrong sheet number', line, _sch_line_number)
                self.sheet = int(res[0])
                self.sheets = int(res[1])
            else:
                m = re.match(r'(\S+)\s+"(.*)"', line)
                if not m:
                    raise SchFileError('Wrong entry in title block', line, _sch_line_number)
                self.title_block[m.group(1)] = m.group(2)

    def load(self, fname, sheet_path=''):
        """ Load a v5.x KiCad Schematic.
            The caller must be sure the file exists. """
        logger.debug("Loading sheet from "+fname)
        self.fname = fname
        with open(fname, 'rt') as f:
            global _sch_line_number
            _sch_line_number = 0
            line = _get_line(f)
            m = re.match(r'EESchema Schematic File Version (\d+)', line)
            if not m:
                raise SchFileError('No eeschema signature', line, _sch_line_number)
            self.version = int(m.group(1))
            line = _get_line(f)
            if line.startswith('LIBS'):
                # LIBS is optional and can be skipped
                line = _get_line(f)
            m = re.match(r'EELAYER (\d+) (\d+)', line, _sch_line_number)
            if not m:
                raise SchFileError('Missing EELAYER', line, _sch_line_number)
            self.eelayer_n = int(m.group(1))
            self.eelayer_m = int(m.group(2))
            line = _get_line(f)
            if not line.startswith('EELAYER END'):
                raise SchFileError('Missing EELAYER END', line, _sch_line_number)
            self._get_title_block(f)
            line = _get_line(f)
            self.all = []
            self.components = []
            self.conn = []
            self.texts = []
            self.wires = []
            self.bitmaps = []
            self.sheets = []
            while not line.startswith('$EndSCHEMATC'):
                if line.startswith('$Comp'):
                    obj = SchematicComponent.load(f, sheet_path)
                    self.components.append(obj)
                elif line.startswith('NoConn'):
                    obj = SchematicConnection.parse(False, line[7:])
                    self.conn.append(obj)
                elif line.startswith('Connection'):
                    obj = SchematicConnection.parse(True, line[11:])
                    self.conn.append(obj)
                elif line.startswith('Text'):
                    obj = SchematicText.load(f, line)
                    self.texts.append(obj)
                elif line.startswith('Wire') or line.startswith('Entry'):
                    obj = SchematicWire.load(f, line)
                    self.wires.append(obj)
                elif line.startswith('$Bitmap'):
                    obj = SchematicBitmap.load(f)
                    self.bitmaps.append(obj)
                elif line.startswith('$Sheet'):
                    obj = SchematicSheet.load(f)
                    self.sheets.append(obj)
                else:
                    raise SchFileError('Unknown definition', line, _sch_line_number)
                self.all.append(obj)
                line = _get_line(f)
            # Load sub-sheets
            self.sub_sheets = []
            for sch in self.sheets:
                self.sub_sheets.append(sch.load_sheet(fname, sheet_path))

    def get_files(self):
        """ A list of the names for all the sheets, including this one. """
        files = [self.fname]
        for sch in self.sheets:
            files.extend(sch.sheet.get_files())
        return files

    def get_components(self, exclude_power=True):
        """ A list of all the components. """
        if exclude_power:
            components = [c for c in self.components if not c.is_power]
        else:
            components = [c for c in self.components]
        for sch in self.sheets:
            components.extend(sch.sheet.get_components(exclude_power))
        components.sort(key=lambda g: g.ref)
        return components

    def get_field_names(self, fields):
        fields_lc = {v.lower(): 1 for v in fields}
        for c in self.components:
            for f in c.fields:
                name_lc = f.name.lower()
                if name_lc not in fields_lc:
                    fields.append(f.name)
                    fields_lc[name_lc] = 1
        for sch in self.sheets:
            fields = sch.sheet.get_field_names(fields)
        return fields
