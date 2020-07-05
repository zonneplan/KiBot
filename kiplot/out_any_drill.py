import os
from pcbnew import (PLOT_FORMAT_HPGL, PLOT_FORMAT_POST, PLOT_FORMAT_GERBER, PLOT_FORMAT_DXF, PLOT_FORMAT_SVG,
                    PLOT_FORMAT_PDF, wxPoint)
from .optionable import Optionable
from .out_base import BaseOutput
from kiplot.macros import macros, document  # noqa: F401
from . import log

logger = log.get_logger(__name__)


class DrillMap(Optionable):
    def __init__(self, name, description):
        super().__init__(name, description)
        with document:
            self.type = 'pdf'
            """ [hpgl,ps,gerber,dxf,svg,pdf] format for a graphical drill map """


class DrillReport(Optionable):
    def __init__(self, name, description):
        super().__init__(name, description)
        with document:
            self.filename = ''
            """ name of the drill report. Not generated unless a name is specified """


class AnyDrill(BaseOutput):
    def __init__(self, name, type, description):
        super().__init__(name, type, description)
        # Options
        with document:
            self.use_aux_axis_as_origin = False
            """ use the auxiliar axis as origin for coordinates """
            self.map = DrillMap
            """ [dict|string] [hpgl,ps,gerber,dxf,svg,pdf] format for a graphical drill map.
                Not generated unless a format is specified """
            self.report = DrillReport
            """ [dict|string] name of the drill report. Not generated unless a name is specified """  # pragma: no cover
        # Mappings to KiCad values
        self._map_map = {
                         'hpgl': PLOT_FORMAT_HPGL,
                         'ps': PLOT_FORMAT_POST,
                         'gerber': PLOT_FORMAT_GERBER,
                         'dxf': PLOT_FORMAT_DXF,
                         'svg': PLOT_FORMAT_SVG,
                         'pdf': PLOT_FORMAT_PDF
                        }

    def config(self, outdir, options, layers):
        super().config(outdir, options, layers)
        # Solve the map for both cases
        if isinstance(self.map, str):
            self.map = self._map_map[self.map]
        elif isinstance(self.map, DrillMap):
            self.map = self._map_map[self.map.type]
        else:
            self.map = None
        # Solve the report for both cases
        if isinstance(self.report, DrillReport):
            self.report = self.report.filename
        elif not isinstance(self.report, str):
            self.report = None

    def run(self, output_dir, board):
        # dialog_gendrill.cpp:357
        if self.use_aux_axis_as_origin:
            offset = board.GetAuxOrigin()
        else:
            offset = wxPoint(0, 0)
        drill_writer = self._configure_writer(board, offset)

        logger.debug("Generating drill files in "+output_dir)
        gen_map = self.map is not None
        if gen_map:
            drill_writer.SetMapFileFormat(self.map)
            logger.debug("Generating drill map type {} in {}".format(self.map, output_dir))
        # We always generate the drill file
        drill_writer.CreateDrillandMapFilesSet(output_dir, True, gen_map)

        if self.report:
            drill_report_file = os.path.join(output_dir, self.report)
            logger.debug("Generating drill report: "+drill_report_file)
            drill_writer.GenDrillReportFile(drill_report_file)
