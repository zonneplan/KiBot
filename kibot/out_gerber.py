# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2018 John Beard
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot
from pcbnew import (PLOT_FORMAT_GERBER, FromMM, ToMM)
from .gs import GS
from .misc import KICAD_VERSION_5_99
from .out_any_layer import (AnyLayer, AnyLayerOptions)
from .error import KiPlotConfigurationError
from .macros import macros, document, output_class  # noqa: F401


class GerberOptions(AnyLayerOptions):
    def __init__(self):
        with document:
            self.use_aux_axis_as_origin = False
            """ Use the auxiliary axis as origin for coordinates """
            self.line_width = 0.1
            """ [0.02,2] Line_width for objects without width [mm] (KiCad 5) """
            self.subtract_mask_from_silk = False
            """ Substract the solder mask from the silk screen """
            self.use_protel_extensions = False
            """ Use legacy Protel file extensions """
            self._gerber_precision = 4.6
            """ This the gerber coordinate format, can be 4.5 or 4.6 """
            self.create_gerber_job_file = True
            """ Creates a file with information about all the generated gerbers.
                You can use it in gerbview to load all gerbers at once """
            self.gerber_job_file = GS.def_global_output
            """ Name for the gerber job file (%i='job', %x='gbrjob') """
            self.use_gerber_x2_attributes = True
            """ Use the extended X2 format (otherwise use X1 formerly RS-274X) """
            self.use_gerber_net_attributes = True
            """ Include netlist metadata """
            self.disable_aperture_macros = False
            """ Disable aperture macros (workaround for buggy CAM software) (KiCad 6) """
        super().__init__()
        self._plot_format = PLOT_FORMAT_GERBER

    @property
    def gerber_precision(self):
        return self._gerber_precision

    @gerber_precision.setter
    def gerber_precision(self, val):
        if val != 4.5 and val != 4.6:
            raise KiPlotConfigurationError("`gerber_precision` must be 4.5 or 4.6")
        self._gerber_precision = val

    def _configure_plot_ctrl(self, po, output_dir):
        super()._configure_plot_ctrl(po, output_dir)
        po.SetSubtractMaskFromSilk(self.subtract_mask_from_silk)
        po.SetUseGerberProtelExtensions(self.use_protel_extensions)
        po.SetGerberPrecision(5 if self.gerber_precision == 4.5 else 6)
        po.SetCreateGerberJobFile(self.create_gerber_job_file)
        po.SetUseGerberX2format(self.use_gerber_x2_attributes)
        po.SetIncludeGerberNetlistInfo(self.use_gerber_net_attributes)
        po.SetUseAuxOrigin(self.use_aux_axis_as_origin)
        po.SetDrillMarksType(0)
        if GS.kicad_version_n < KICAD_VERSION_5_99:
            po.SetLineWidth(FromMM(self.line_width))
        else:
            po.SetDisableGerberMacros(self.disable_aperture_macros)  # pragma: no cover (Ki6)
        setattr(po, 'gerber_job_file', self.gerber_job_file)

    def read_vals_from_po(self, po):
        super().read_vals_from_po(po)
        # usegerberattributes
        self.use_gerber_x2_attributes = po.GetUseGerberX2format()
        # usegerberextensions
        self.use_protel_extensions = po.GetUseGerberProtelExtensions()
        # usegerberadvancedattributes
        self.use_gerber_net_attributes = po.GetIncludeGerberNetlistInfo()
        # creategerberjobfile
        self.create_gerber_job_file = po.GetCreateGerberJobFile()
        # gerberprecision
        self.gerber_precision = 4.0 + po.GetGerberPrecision()/10.0
        # subtractmaskfromsilk
        self.subtract_mask_from_silk = po.GetSubtractMaskFromSilk()
        # useauxorigin
        self.use_aux_axis_as_origin = po.GetUseAuxOrigin()
        if GS.kicad_version_n < KICAD_VERSION_5_99:
            # linewidth
            self.line_width = ToMM(po.GetLineWidth())
        else:
            # disableapertmacros
            self.disable_aperture_macros = po.GetDisableGerberMacros()  # pragma: no cover (Ki6)


@output_class
class Gerber(AnyLayer):
    """ Gerber format
        This is the main fabrication format for the PCB.
        This output is what you get from the File/Plot menu in pcbnew. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = GerberOptions
            """ [dict] Options for the `gerber` output """
