# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2019 Romain Deterre (@rdeterre)
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot/pull/10
import operator
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

    def config(self):
        super().config()
        if not self.id:
            raise KiPlotConfigurationError("Missing or empty `id` in columns list ({})".format(str(self._tree)))


class PositionOptions(VariantOptions):
    def __init__(self):
        with document:
            self.format = 'ASCII'
            """ [ASCII,CSV] format for the position file """
            self.separate_files_for_front_and_back = True
            """ generate two separated files, one for the top and another for the bottom """
            self.only_smd = True
            """ only include the surface mount components """
            self.output = GS.def_global_output
            """ output file name (%i='top_pos'|'bottom_pos'|'both_pos', %x='pos'|'csv') """
            self.units = 'millimeters'
            """ [millimeters,inches] units used for the positions """
            self.columns = PosColumns
            """ [list(dict)|list(string)] which columns are included in the output """
        super().__init__()

    def config(self):
        super().config()
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

    def _do_position_plot_ascii(self, board, output_dir, columns, modulesStr, maxSizes):
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

    def _do_position_plot_csv(self, board, output_dir, columns, modulesStr):
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
            fle.write(",".join('"{}"'.format(e) for e in m))
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
        return m.GetAttributes() & (MOD_THROUGH_HOLE | MOD_SMD) == MOD_SMD

    @staticmethod
    def is_not_virtual_5(m):
        return m.GetAttributes() != UI_VIRTUAL

    @staticmethod
    def is_not_virtual_6(m):
        return not (m.GetAttributes() & MOD_EXCLUDE_FROM_POS_FILES)

    def run(self, output_dir, board):
        super().run(output_dir, board)
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
        if GS.kicad_version_n < KICAD_VERSION_5_99:
            is_pure_smd = self.is_pure_smd_5
            is_not_virtual = self.is_not_virtual_5
        else:
            is_pure_smd = self.is_pure_smd_6
            is_not_virtual = self.is_not_virtual_6
        for m in sorted(board.GetModules(), key=operator.methodcaller('GetReference')):
            ref = m.GetReference()
            # Apply any filter or variant data
            if comps_hash:
                c = comps_hash.get(ref, None)
                if c and (not c.fitted or not c.included):
                    continue
            # If passed check the position options
            if (self.only_smd and is_pure_smd(m)) or (not self.only_smd and is_not_virtual(m)):
                center = m.GetCenter()
                # KiCad: PLACE_FILE_EXPORTER::GenPositionData() in export_footprints_placefile.cpp
                row = []
                for k in self.columns:
                    if k == 'Ref':
                        row.append(ref)
                    elif k == 'Val':
                        row.append(m.GetValue())
                    elif k == 'Package':
                        row.append(str(m.GetFPID().GetLibItemName()))  # pcbnew.UTF8 type
                    elif k == 'PosX':
                        row.append("{:.4f}".format(center.x * conv))
                    elif k == 'PosY':
                        row.append("{:.4f}".format(-center.y * conv))
                    elif k == 'Rot':
                        row.append("{:.4f}".format(m.GetOrientationDegrees()))
                    elif k == 'Side':
                        row.append("bottom" if m.IsFlipped() else "top")
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
            self._do_position_plot_ascii(board, output_dir, columns, modules, maxlengths)
        else:  # if self.format == 'CSV':
            self._do_position_plot_csv(board, output_dir, columns, modules)


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
