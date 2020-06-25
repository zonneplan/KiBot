import os
from pcbnew import (PLOT_FORMAT_HPGL, PLOT_FORMAT_POST, PLOT_FORMAT_GERBER, PLOT_FORMAT_DXF, PLOT_FORMAT_SVG,
                    PLOT_FORMAT_PDF, wxPoint)
from .out_base import BaseOutput
from .error import KiPlotConfigurationError
from kiplot.macros import macros, document  # noqa: F401
from . import log

logger = log.get_logger(__name__)


class AnyDrill(BaseOutput):
    def __init__(self, name, type, description):
        super(AnyDrill, self).__init__(name, type, description)
        # Options
        with document:
            self.use_aux_axis_as_origin = False
            """ use the auxiliar axis as origin for coordinates """
            self._map = None
            """ [string=None] format for a graphical drill map. The valid formats are hpgl, ps, gerber, dxf, svg and pdf.
                Not generated unless a format is specified """
            self._report = None
            """ [string=None] name of the drill report. Not generated unless a name is specified """
        # Mappings to KiCad values
        self._map_map = {
                         'hpgl': PLOT_FORMAT_HPGL,
                         'ps': PLOT_FORMAT_POST,
                         'gerber': PLOT_FORMAT_GERBER,
                         'dxf': PLOT_FORMAT_DXF,
                         'svg': PLOT_FORMAT_SVG,
                         'pdf': PLOT_FORMAT_PDF
                        }

    @property
    def map(self):
        return self._map

    @map.setter
    def map(self, val):
        # In the original "version 1" of the format this is a dict with one key named `type`.
        # Currently we spect a string, but we support the old mechanism.
        if val is None:
            raise KiPlotConfigurationError("Empty drill `map` section")
        # Setting from a dict
        if isinstance(val, dict):
            if 'type' not in val:
                raise KiPlotConfigurationError("drill `map` must contain a `type`")
            type = val['type']
            if not isinstance(type, str):
                raise KiPlotConfigurationError("drill `map` `type` must be a string")
            val = type
        if val not in self._map_map:
            raise KiPlotConfigurationError("Unknown drill `map` `type`: {}".format(val))
        self._map = val

    @property
    def report(self):
        return self._report

    @report.setter
    def report(self, val):
        # In the original "version 1" of the format this is a dict with one key named `filename`.
        # Currently we spect a string, but we support the old mechanism.
        if val is None:
            raise KiPlotConfigurationError("Empty drill `report` section")
        # Setting from a dict
        if isinstance(val, dict):
            if 'filename' not in val:
                raise KiPlotConfigurationError("drill `report` must contain a `filename`")
            filename = val['filename']
            if not isinstance(filename, str):
                raise KiPlotConfigurationError("drill `report` `filename` must be a string")
            val = filename
        self._report = val

    def config(self, outdir, options, layers):
        super().config(outdir, options, layers)
        if self._map:
            self._map = self._map_map[self._map]

    def run(self, output_dir, board):
        # dialog_gendrill.cpp:357
        if self.use_aux_axis_as_origin:
            offset = board.GetAuxOrigin()
        else:
            offset = wxPoint(0, 0)
        drill_writer = self._configure_writer(board, offset)

        logger.debug("Generating drill files in "+output_dir)
        gen_map = self._map is not None
        if gen_map:
            drill_writer.SetMapFileFormat(self._map)
            logger.debug("Generating drill map type {} in {}".format(self._map, output_dir))
        # We always generate the drill file
        drill_writer.CreateDrillandMapFilesSet(output_dir, True, gen_map)

        if self._report is not None:
            drill_report_file = os.path.join(output_dir, self._report)
            logger.debug("Generating drill report: "+drill_report_file)
            drill_writer.GenDrillReportFile(drill_report_file)
