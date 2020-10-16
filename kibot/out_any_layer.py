# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2018 John Beard
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot
import os
from pcbnew import GERBER_JOBFILE_WRITER, PLOT_CONTROLLER, IsCopperLayer
from .out_base import (BaseOutput)
from .error import (PlotError, KiPlotConfigurationError)
from .layer import Layer
from .gs import GS
from .misc import KICAD_VERSION_5_99
from .out_base import VariantOptions
from .macros import macros, document  # noqa: F401
from . import log

logger = log.get_logger(__name__)


class AnyLayerOptions(VariantOptions):
    """ Base class for: DXF, Gerber, HPGL, PDF, PS and SVG """
    def __init__(self):
        with document:
            self.exclude_edge_layer = True
            """ do not include the PCB edge layer """
            self.exclude_pads_from_silkscreen = False
            """ do not plot the component pads in the silk screen (KiCad 5.x only) """
            self.plot_sheet_reference = False
            """ currently without effect """
            self.plot_footprint_refs = True
            """ include the footprint references """
            self.plot_footprint_values = True
            """ include the footprint values """
            self.force_plot_invisible_refs_vals = False
            """ include references and values even when they are marked as invisible """
            self.output = GS.def_global_output
            """ output file name, the default KiCad name if empty """
            self.tent_vias = True
            """ cover the vias """
        super().__init__()

    def _configure_plot_ctrl(self, po, output_dir):
        logger.debug("Configuring plot controller for output")
        po.SetOutputDirectory(output_dir)
        po.SetPlotFrameRef(self.plot_sheet_reference)
        po.SetPlotReference(self.plot_footprint_refs)
        po.SetPlotValue(self.plot_footprint_values)
        po.SetPlotInvisibleText(self.force_plot_invisible_refs_vals)
        po.SetExcludeEdgeLayer(self.exclude_edge_layer)
        if GS.kicad_version_n < KICAD_VERSION_5_99:
            po.SetPlotPadsOnSilkLayer(not self.exclude_pads_from_silkscreen)
        po.SetPlotViaOnMaskLayer(not self.tent_vias)
        # Only useful for gerber outputs
        po.SetCreateGerberJobFile(False)
        # We'll come back to this on a per-layer basis
        po.SetSkipPlotNPTH_Pads(False)

    def filter_components(self, board):
        """  Apply the variants and filters """
        if not self._comps:
            return None
        self.comps_hash = self.get_refs_hash()
        self.cross_modules(board, self.comps_hash)
        return self.remove_paste_and_glue(board, self.comps_hash)

    def unfilter_components(self, board):
        self.uncross_modules(board, self.comps_hash)
        self.restore_paste_and_glue(board, self.comps_hash)

    def run(self, output_dir, board, layers):
        super().run(output_dir, board)
        # fresh plot controller
        plot_ctrl = PLOT_CONTROLLER(board)
        # set up plot options for the whole output
        po = plot_ctrl.GetPlotOptions()
        self._configure_plot_ctrl(po, output_dir)
        # Gerber Job files aren't automagically created
        # We need to assist KiCad
        create_job = po.GetCreateGerberJobFile()
        if create_job:
            jobfile_writer = GERBER_JOBFILE_WRITER(board)
        plot_ctrl.SetColorMode(True)
        # Apply the variants and filters
        exclude = self.filter_components(board)
        # Plot every layer in the output
        layers = Layer.solve(layers)
        for la in layers:
            suffix = la.suffix
            desc = la.description
            id = la.id
            # Set current layer
            plot_ctrl.SetLayer(id)
            # Skipping NPTH is controlled by whether or not this is
            # a copper layer
            is_cu = IsCopperLayer(id)
            po.SetSkipPlotNPTH_Pads(is_cu)
            # Plot single layer to file
            logger.debug("Opening plot file for layer `{}` format `{}`".format(la, self._plot_format))
            if not plot_ctrl.OpenPlotfile(suffix, self._plot_format, desc):
                # Shouldn't happen
                raise PlotError("OpenPlotfile failed!")  # pragma: no cover
            # Compute the current file name and the one we want
            k_filename = plot_ctrl.GetPlotFileName()
            if self.output:
                filename = self.expand_filename(output_dir, self.output, suffix, os.path.splitext(k_filename)[1][1:])
            else:
                filename = k_filename
            logger.debug("Plotting layer `{}` to `{}`".format(la, filename))
            plot_ctrl.PlotLayer()
            plot_ctrl.ClosePlot()
            if self.output:
                os.rename(k_filename, filename)
            if create_job:
                jobfile_writer.AddGbrFile(id, os.path.basename(filename))
        # Create the job file
        if create_job:
            jobfile_writer.CreateJobFile(self.expand_filename(output_dir, po.gerber_job_file, 'job', 'gbrjob'))
        # Restore the eliminated layers
        if exclude:
            self.unfilter_components(board)

    def read_vals_from_po(self, po):
        # excludeedgelayer
        self.exclude_edge_layer = po.GetExcludeEdgeLayer()
        # plotframeref
        self.plot_sheet_reference = po.GetPlotFrameRef()
        # plotreference
        self.plot_footprint_refs = po.GetPlotReference()
        # plotvalue
        self.plot_footprint_values = po.GetPlotValue()
        # plotinvisibletext
        self.force_plot_invisible_refs_vals = po.GetPlotInvisibleText()
        # viasonmask
        self.tent_vias = not po.GetPlotViaOnMaskLayer()
        if GS.kicad_version_n < KICAD_VERSION_5_99:
            # padsonsilk
            self.exclude_pads_from_silkscreen = not po.GetPlotPadsOnSilkLayer()


class AnyLayer(BaseOutput):
    def __init__(self):
        super().__init__()
        with document:
            self.layers = Layer
            """ [list(dict)|list(string)|string] [all,selected,copper,technical,user]
                List of PCB layers to plot """

    def config(self):
        super().config()
        # We need layers
        if isinstance(self.layers, type):
            raise KiPlotConfigurationError("Missing `layers` list")

    def run(self, output_dir, board):
        self.options.run(output_dir, board, self.layers)
