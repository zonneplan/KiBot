# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2019 Romain Deterre (@rdeterre)
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot/pull/10
import os
from re import compile
from datetime import datetime
from pcbnew import IU_PER_MM, IU_PER_MILS
from collections import OrderedDict
from .gs import GS
from .misc import UI_SMD, UI_VIRTUAL, KICAD_VERSION_5_99, MOD_THROUGH_HOLE, MOD_SMD, MOD_EXCLUDE_FROM_POS_FILES
from .optionable import Optionable
from .out_base import VariantOptions
from .error import KiPlotConfigurationError
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger(__name__)
ref_re = compile(r'([^\d]+)([\?\d]+)')


def _ref_key(ref_str):
    """ Splits a reference intro prefix and suffix.
        Helps to sort references in a natural way. """
    m = ref_re.match(ref_str)
    if not m:
        return [ref_str]
    pre, suf = m.groups()
    return [pre, 0 if suf == '?' else int(suf)]


class PosColumns(Optionable):
    """ Which columns we want and its names """
    def __init__(self):
        super().__init__()
        self._unkown_is_error = True
        with document:
            self.id = ''
            """ [Ref,Val,Package,PosX,PosY,Rot,Side] Internal name """
            self.name = ''
            """ Name to use in the outut file. The id is used when empty """
        self._id_example = 'Ref'
        self._name_example = 'Reference'

    def config(self, parent):
        super().config(parent)
        if not self.id:
            raise KiPlotConfigurationError("Missing or empty `id` in columns list ({})".format(str(self._tree)))


class PositionOptions(VariantOptions):
    def __init__(self):
        with document:
            self.format = 'ASCII'
            """ [ASCII,CSV] Format for the position file """
            self.separate_files_for_front_and_back = True
            """ Generate two separated files, one for the top and another for the bottom """
            self.only_smd = True
            """ Only include the surface mount components """
            self.output = GS.def_global_output
            """ Output file name (%i='top_pos'|'bottom_pos'|'both_pos', %x='pos'|'csv') """
            self.units = 'millimeters'
            """ [millimeters,inches] Units used for the positions """
            self.columns = PosColumns
            """ [list(dict)|list(string)] Which columns are included in the output """
            self.bottom_negative_x = False
            """ Use negative X coordinates for footprints on bottom layer """
        super().__init__()
        self._expand_id = 'position'

    def config(self, parent):
        super().config(parent)
        if isinstance(self.columns, type):
            # Default list of columns
            self.columns = OrderedDict([('Ref', 'Ref'), ('Val', 'Val'), ('Package', 'Package'), ('PosX', 'PosX'),
                                        ('PosY', 'PosY'), ('Rot', 'Rot'), ('Side', 'Side')])
        else:
            new_columns = OrderedDict()
            for col in self.columns:
                if isinstance(col, str):
                    # Just a string, add to the list of used
                    new_name = new_col = col
                else:
                    new_col = col.id
                    new_name = col.name if col.name else new_col
                new_columns[new_col] = new_name
            self.columns = new_columns
        self._expand_ext = 'pos' if self.format == 'ASCII' else 'csv'

    def _do_position_plot_ascii(self, output_dir, columns, modulesStr, maxSizes):
        topf = None
        botf = None
        bothf = None
        if self.separate_files_for_front_and_back:
            topf = open(self.expand_filename(output_dir, self.output, 'top_pos', 'pos'), 'w')
            botf = open(self.expand_filename(output_dir, self.output, 'bottom_pos', 'pos'), 'w')
        else:
            bothf = open(self.expand_filename(output_dir, self.output, 'both_pos', 'pos'), 'w')

        files = [f for f in [topf, botf, bothf] if f is not None]
        for f in files:
            f.write('### Module positions - created on {} ###\n'.format(datetime.now().strftime("%a %d %b %Y %X %Z")))
            f.write('### Printed by KiBot\n')
            unit = {'millimeters': 'mm', 'inches': 'in'}[self.units]
            f.write('## Unit = {}, Angle = deg.\n'.format(unit))

        if topf is not None:
            topf.write('## Side : top\n')
        if botf is not None:
            botf.write('## Side : bottom\n')
        if bothf is not None:
            bothf.write('## Side : both\n')

        for f in files:
            f.write('# ')
            for idx, col in enumerate(columns):
                if idx > 0:
                    f.write("   ")
                f.write("{0: <{width}}".format(col, width=maxSizes[idx]))
            f.write('\n')

        # Account for the "# " at the start of the comment column
        maxSizes[0] = maxSizes[0] + 2

        for m in modulesStr:
            fle = bothf
            if fle is None:
                if m[-1] == "top":
                    fle = topf
                else:
                    fle = botf
            for idx, col in enumerate(m):
                if idx > 0:
                    fle.write("   ")
                fle.write("{0: <{width}}".format(col, width=maxSizes[idx]))
            fle.write("\n")

        for f in files:
            f.write("## End\n")

        if topf is not None:
            topf.close()
        if botf is not None:
            botf.close()
        if bothf is not None:
            bothf.close()

    def _do_position_plot_csv(self, output_dir, columns, modulesStr):
        topf = None
        botf = None
        bothf = None
        if self.separate_files_for_front_and_back:
            topf = open(self.expand_filename(output_dir, self.output, 'top_pos', 'csv'), 'w')
            botf = open(self.expand_filename(output_dir, self.output, 'bottom_pos', 'csv'), 'w')
        else:
            bothf = open(self.expand_filename(output_dir, self.output, 'both_pos', 'csv'), 'w')

        files = [f for f in [topf, botf, bothf] if f is not None]

        for f in files:
            f.write(",".join(columns))
            f.write("\n")

        for m in modulesStr:
            fle = bothf
            if fle is None:
                if m[-1] == "top":
                    fle = topf
                else:
                    fle = botf
            fle.write(",".join('{}'.format(e) for e in m))
            fle.write("\n")

        if topf is not None:
            topf.close()
        if botf is not None:
            botf.close()
        if bothf is not None:
            bothf.close()

    @staticmethod
    def is_pure_smd_5(m):
        return m.GetAttributes() == UI_SMD

    @staticmethod
    def is_pure_smd_6(m):
        return m.GetAttributes() & (MOD_THROUGH_HOLE | MOD_SMD) == MOD_SMD  # pragma: no cover (Ki6)

    @staticmethod
    def is_not_virtual_5(m):
        return m.GetAttributes() != UI_VIRTUAL

    @staticmethod
    def is_not_virtual_6(m):
        return not (m.GetAttributes() & MOD_EXCLUDE_FROM_POS_FILES)  # pragma: no cover (Ki6)

    @staticmethod
    def get_attr_tests():
        if GS.kicad_version_n < KICAD_VERSION_5_99:
            return PositionOptions.is_pure_smd_5, PositionOptions.is_not_virtual_5
        return PositionOptions.is_pure_smd_6, PositionOptions.is_not_virtual_6  # pragma: no cover (Ki6)

    def get_targets(self, out_dir):
        ext = self._expand_ext
        if self.separate_files_for_front_and_back:
            return [self.expand_filename(out_dir, self.output, 'top_pos', ext),
                    self.expand_filename(out_dir, self.output, 'bottom_pos', ext)]
        return [self.expand_filename(out_dir, self.output, 'both_pos', ext)]

    def run(self, fname):
        super().run(fname)
        output_dir = os.path.dirname(fname)
        columns = self.columns.values()
        # Note: the parser already checked the units are milimeters or inches
        conv = 1.0
        if self.units == 'millimeters':
            conv = 1.0 / IU_PER_MM
        else:  # self.units == 'inches':
            conv = 0.001 / IU_PER_MILS
        # Format all strings
        comps_hash = self.get_refs_hash()
        modules = []
        is_pure_smd, is_not_virtual = self.get_attr_tests()
        quote_char = '"' if self.format == 'CSV' else ''
        for m in sorted(GS.board.GetModules(), key=lambda c: _ref_key(c.GetReference())):
            ref = m.GetReference()
            logger.debug('P&P ref: {}'.format(ref))
            value = None
            # Apply any filter or variant data
            if comps_hash:
                c = comps_hash.get(ref, None)
                if c:
                    logger.debug('fit: {} include: {}'.format(c.fitted, c.included))
                    if not c.fitted or not c.included:
                        continue
                    value = c.value
                    footprint = c.footprint
                    is_bottom = c.bottom
                    rotation = c.footprint_rot
            if value is None:
                value = m.GetValue()
                footprint = str(m.GetFPID().GetLibItemName())  # pcbnew.UTF8 type
                is_bottom = m.IsFlipped()
                rotation = m.GetOrientationDegrees()
            # If passed check the position options
            if (self.only_smd and is_pure_smd(m)) or (not self.only_smd and is_not_virtual(m)):
                center = m.GetCenter()
                # KiCad: PLACE_FILE_EXPORTER::GenPositionData() in export_footprints_placefile.cpp
                row = []
                for k in self.columns:
                    if k == 'Ref':
                        row.append(quote_char+ref+quote_char)
                    elif k == 'Val':
                        row.append(quote_char+value+quote_char)
                    elif k == 'Package':
                        row.append(quote_char+footprint+quote_char)
                    elif k == 'PosX':
                        pos_x = center.x * conv
                        if self.bottom_negative_x and is_bottom:
                            pos_x = -pos_x
                        row.append("{:.4f}".format(pos_x))
                    elif k == 'PosY':
                        row.append("{:.4f}".format(-center.y * conv))
                    elif k == 'Rot':
                        row.append("{:.4f}".format(rotation))
                    elif k == 'Side':
                        row.append("bottom" if is_bottom else "top")
                modules.append(row)
        # Find max width for all columns
        maxlengths = []
        for col, name in enumerate(columns):
            max_l = len(name)
            for row in modules:
                max_l = max(max_l, len(row[col]))
            maxlengths.append(max_l)
        # Note: the parser already checked the format is ASCII or CSV
        if self.format == 'ASCII':
            self._do_position_plot_ascii(output_dir, columns, modules, maxlengths)
        else:  # if self.format == 'CSV':
            self._do_position_plot_csv(output_dir, columns, modules)


@output_class
class Position(BaseOutput):  # noqa: F821
    """ Pick & place
        Generates the file with position information for the PCB components, used by the pick and place machine.
        This output is what you get from the 'File/Fabrication output/Footprint poistion (.pos) file' menu in pcbnew. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = PositionOptions
            """ [dict] Options for the `position` output """
