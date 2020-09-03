# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2018 John Beard
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot
import os
from pcbnew import GERBER_JOBFILE_WRITER, PLOT_CONTROLLER, IsCopperLayer, LSET
from .out_base import (BaseOutput)
from .error import (PlotError, KiPlotConfigurationError)
from .optionable import BaseOptions, Optionable
from .registrable import RegOutput
from .layer import Layer
from .gs import GS
from .misc import UI_VIRTUAL
from .kiplot import load_sch
from .macros import macros, document  # noqa: F401
from .fil_base import BaseFilter, apply_fitted_filter
from . import log

logger = log.get_logger(__name__)


class AnyLayerOptions(BaseOptions):
    """ Base class for: DXF, Gerber, HPGL, PDF, PS and SVG """
    def __init__(self):
        with document:
            self.exclude_edge_layer = True
            """ do not include the PCB edge layer """
            self.exclude_pads_from_silkscreen = False
            """ do not plot the component pads in the silk screen """
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
            self.variant = ''
            """ Board variant(s) to apply """
            self.dnf_filter = Optionable
            """ [string|list(string)=''] Name of the filter to mark components as not fitted.
                A short-cut to use for simple cases where a variant is an overkill """
        super().__init__()

    def config(self):
        super().config()
        self.variant = RegOutput.check_variant(self.variant)
        self.dnf_filter = BaseFilter.solve_filter(self.dnf_filter, 'dnf_filter')

    def _configure_plot_ctrl(self, po, output_dir):
        logger.debug("Configuring plot controller for output")
        po.SetOutputDirectory(output_dir)
        po.SetPlotFrameRef(self.plot_sheet_reference)
        po.SetPlotReference(self.plot_footprint_refs)
        po.SetPlotValue(self.plot_footprint_values)
        po.SetPlotInvisibleText(self.force_plot_invisible_refs_vals)
        po.SetExcludeEdgeLayer(self.exclude_edge_layer)
        po.SetPlotPadsOnSilkLayer(not self.exclude_pads_from_silkscreen)
        po.SetPlotViaOnMaskLayer(not self.tent_vias)
        # Only useful for gerber outputs
        po.SetCreateGerberJobFile(False)
        # We'll come back to this on a per-layer basis
        po.SetSkipPlotNPTH_Pads(False)

    def filter_components(self, board):
        # Apply the variants and filters
        exclude = None
        if hasattr(self, 'variant') and (self.dnf_filter or self.variant):
            load_sch()
            # Get the components list from the schematic
            comps = GS.sch.get_components()
            # Apply the filter
            apply_fitted_filter(comps, self.dnf_filter)
            # Apply the variant
            if self.variant:
                # Apply the variant
                self.variant.filter(comps)
            comps_hash = {c.ref: c for c in comps}
            # Remove from solder past layers the filtered components
            exclude = LSET()
            exclude.addLayer(board.GetLayerID('F.Paste'))
            exclude.addLayer(board.GetLayerID('B.Paste'))
            old_layers = []
            fadhes = board.GetLayerID('F.Adhes')
            badhes = board.GetLayerID('B.Adhes')
            old_fadhes = []
            old_badhes = []
            for m in board.GetModules():
                ref = m.GetReference()
                c = comps_hash.get(ref, None)
                if (c and not c.fitted) or m.GetAttributes() == UI_VIRTUAL:
                    # Remove all pads from *.Paste
                    old_c_layers = []
                    for p in m.Pads():
                        pad_layers = p.GetLayerSet()
                        old_c_layers.append(pad_layers.FmtHex())
                        pad_layers.removeLayerSet(exclude)
                        p.SetLayerSet(pad_layers)
                    old_layers.append(old_c_layers)
                    # Remove any graphical item in the *.Adhes layers
                    for gi in m.GraphicalItems():
                        l_gi = gi.GetLayer()
                        if l_gi == fadhes:
                            gi.SetLayer(-1)
                            old_fadhes.append(gi)
                        if l_gi == badhes:
                            gi.SetLayer(-1)
                            old_badhes.append(gi)
                        # if gi.GetClass() == 'MGRAPHIC':
                        #     logger.debug(gi.GetShapeStr())
            self.comps_hash = comps_hash
            self.old_layers = old_layers
            self.old_fadhes = old_fadhes
            self.old_badhes = old_badhes
        return exclude

    def unfilter_components(self, board):
        for m in board.GetModules():
            ref = m.GetReference()
            c = self.comps_hash.get(ref, None)
            if (c and not c.fitted) or m.GetAttributes() == UI_VIRTUAL:
                restore = self.old_layers.pop(0)
                for p in m.Pads():
                    pad_layers = p.GetLayerSet()
                    res = restore.pop(0)
                    pad_layers.ParseHex(res, len(res))
                    p.SetLayerSet(pad_layers)
        fadhes = board.GetLayerID('F.Adhes')
        for gi in self.old_fadhes:
            gi.SetLayer(fadhes)
        badhes = board.GetLayerID('B.Adhes')
        for gi in self.old_badhes:
            gi.SetLayer(badhes)

    def run(self, output_dir, board, layers):
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
