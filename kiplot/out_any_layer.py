import os
from pcbnew import (GERBER_JOBFILE_WRITER, PCB_PLOT_PARAMS, FromMM, PLOT_CONTROLLER, IsCopperLayer, SKETCH)
from .out_base import (BaseOutput)
from .error import (PlotError, KiPlotConfigurationError)
from .kiplot import (GS)
from kiplot.macros import macros, document  # noqa: F401
from . import log

logger = log.get_logger(__name__)
AUTO_SCALE = 0


class AnyLayer(BaseOutput):
    def __init__(self, name, type, description):
        super(AnyLayer, self).__init__(name, type, description)
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
        # Mappings to KiCad values
        self._drill_marks_map = {
                                 'none': PCB_PLOT_PARAMS.NO_DRILL_SHAPE,
                                 'small': PCB_PLOT_PARAMS.SMALL_DRILL_SHAPE,
                                 'full': PCB_PLOT_PARAMS.FULL_DRILL_SHAPE,
                                }

    def config(self, outdir, options, layers):
        super().config(outdir, options, layers)
        # We need layers
        if not self._layers:
            raise KiPlotConfigurationError("Missing `layers` list")

    def _configure_plot_ctrl(self, po, output_dir):
        logger.debug("Configuring plot controller for output")
        po.SetOutputDirectory(output_dir)
        po.SetLineWidth(FromMM(self.get_line_width()))
        # Scaling/Autoscale
        scaling = self.get_scaling()
        if scaling == AUTO_SCALE:
            po.SetAutoScale(True)
            po.SetScale(1)
        else:
            po.SetAutoScale(False)
            po.SetScale(scaling)
        po.SetMirror(self.get_mirror_plot())
        po.SetNegative(self.get_negative_plot())
        po.SetPlotFrameRef(self.plot_sheet_reference)
        po.SetPlotReference(self.plot_footprint_refs)
        po.SetPlotValue(self.plot_footprint_values)
        po.SetPlotInvisibleText(self.force_plot_invisible_refs_vals)
        po.SetExcludeEdgeLayer(self.exclude_edge_layer)
        po.SetPlotPadsOnSilkLayer(not self.exclude_pads_from_silkscreen)
        po.SetUseAuxOrigin(self.get_use_aux_axis_as_origin())
        po.SetPlotViaOnMaskLayer(not self.tent_vias)
        # in general, false, but gerber will set it back later
        po.SetUseGerberAttributes(False)
        # Only useful for gerber outputs
        po.SetCreateGerberJobFile(False)
        # How we draw drill marks
        po.SetDrillMarksType(self.get_drill_marks())
        # We'll come back to this on a per-layer basis
        po.SetSkipPlotNPTH_Pads(False)
        if self.get_sketch_plot():
            po.SetPlotMode(SKETCH)

    def get_plot_format(self):
        return self._plot_format

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
            id = l.id
            # for inner layers, we can now check if the layer exists
            if l.is_inner:
                if id < 1 or id >= layer_cnt - 1:
                    raise PlotError("Inner layer `{}` is not valid for this board".format(l))
            # Set current layer
            plot_ctrl.SetLayer(id)
            # Skipping NPTH is controlled by whether or not this is
            # a copper layer
            is_cu = IsCopperLayer(id)
            po.SetSkipPlotNPTH_Pads(is_cu)

            plot_format = self.get_plot_format()

            # Plot single layer to file
            logger.debug("Opening plot file for layer `{}` format `{}`".format(l, plot_format))
            if not plot_ctrl.OpenPlotfile(suffix, plot_format, desc):
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

    # Default values
    # We concentrate all the KiCad plot initialization in one place.
    # Here we provide default values for settings not contained in an output object
    # TODO: avoid them?
    def get_line_width(self):
        return self.line_width if 'line_width' in self.__dict__ else 0

    def get_scaling(self):
        return self.scaling if 'scaling' in self.__dict__ else 1

    def get_mirror_plot(self):
        return self.mirror_plot if 'mirror_plot' in self.__dict__ else False

    def get_negative_plot(self):
        return self.negative_plot if 'negative_plot' in self.__dict__ else False

    def get_use_aux_axis_as_origin(self):
        return self.use_aux_axis_as_origin if 'use_aux_axis_as_origin' in self.__dict__ else False

    def get_drill_marks(self):
        return self.drill_marks if '_drill_marks' in self.__dict__ else PCB_PLOT_PARAMS.NO_DRILL_SHAPE

    def get_sketch_plot(self):
        return self.sketch_plot if 'sketch_plot' in self.__dict__ else False
