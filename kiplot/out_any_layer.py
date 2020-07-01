import os
from pcbnew import (GERBER_JOBFILE_WRITER, PLOT_CONTROLLER, IsCopperLayer)
from .out_base import (BaseOutput)
from .error import (PlotError, KiPlotConfigurationError)
from .gs import (GS)
from kiplot.macros import macros, document  # noqa: F401
from . import log

logger = log.get_logger(__name__)


class AnyLayer(BaseOutput):
    """ Base class for: DXF, Gerber, HPGL, PDF, PS and SVG """
    def __init__(self, name, type, description):
        super(AnyLayer, self).__init__(name, type, description)
        # We need layers, so we define it
        self._layers = None
        # Options
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
            self.tent_vias = True
            """ cover the vias """  # pragma: no cover

    def config(self, outdir, options, layers):
        super().config(outdir, options, layers)
        # We need layers
        if not self._layers:
            raise KiPlotConfigurationError("Missing `layers` list")

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

    def run(self, output_dir, board):
        # fresh plot controller
        plot_ctrl = PLOT_CONTROLLER(board)
        # set up plot options for the whole output
        po = plot_ctrl.GetPlotOptions()
        self._configure_plot_ctrl(po, output_dir)

        layer_cnt = board.GetCopperLayerCount()

        # Gerber Job files aren't automagically created
        # We need to assist KiCad
        create_job = po.GetCreateGerberJobFile()
        if create_job:
            jobfile_writer = GERBER_JOBFILE_WRITER(board)

        plot_ctrl.SetColorMode(True)

        # plot every layer in the output
        for l in self._layers:
            suffix = l.suffix
            desc = l.desc
            id = l.get_layer_id_from_name(layer_cnt)
            # Set current layer
            plot_ctrl.SetLayer(id)
            # Skipping NPTH is controlled by whether or not this is
            # a copper layer
            is_cu = IsCopperLayer(id)
            po.SetSkipPlotNPTH_Pads(is_cu)

            # Plot single layer to file
            logger.debug("Opening plot file for layer `{}` format `{}`".format(l, self._plot_format))
            if not plot_ctrl.OpenPlotfile(suffix, self._plot_format, desc):
                raise PlotError("OpenPlotfile failed!")

            logger.debug("Plotting layer `{}` to `{}`".format(l, plot_ctrl.GetPlotFileName()))
            plot_ctrl.PlotLayer()
            plot_ctrl.ClosePlot()
            if create_job:
                jobfile_writer.AddGbrFile(id, os.path.basename(plot_ctrl.GetPlotFileName()))

        if create_job:
            base_fn = os.path.join(
                         os.path.dirname(plot_ctrl.GetPlotFileName()),
                         os.path.basename(GS.pcb_file))
            base_fn = os.path.splitext(base_fn)[0]
            job_fn = base_fn+'-job.gbrjob'
            jobfile_writer.CreateJobFile(job_fn)

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
