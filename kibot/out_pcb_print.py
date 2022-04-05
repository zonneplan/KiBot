# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2022 Albin Dennevi
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://gitlab.com/dennevi/Board2Pdf/
# Note: Original code released as Public Domain
import os
from pcbnew import PLOT_CONTROLLER, IsCopperLayer, PLOT_FORMAT_PDF
from shutil import rmtree
from tempfile import mkdtemp
from .error import KiPlotConfigurationError
from .gs import GS
from .optionable import Optionable
from .out_base import VariantOptions
from .macros import macros, document, output_class  # noqa: F401
from .layer import Layer
from . import PyPDF2
from . import log

logger = log.get_logger()

# TODO:
# - Se pueden sacar los colores del esquema de colores?
# - Opciones de out_pdf y out_any_layer
# - Estas cosas:
#             self.scaling = 1.0
#             """ Scale factor (0 means autoscaling)"""
#             self._drill_marks = 'full'
#             """ What to use to indicate the drill places, can be none, small or full (for real scale) """
#             self.title = ''
#             """ Text used to replace the sheet title. %VALUE expansions are allowed.
#                 If it starts with `+` the text is concatenated """
#             self.color_theme = '_builtin_classic'
#             """ Selects the color theme. Onlyu applies to KiCad 6.
#                 To use the KiCad 6 default colors select `_builtin_default`.
#                 Usually user colors are stored as `user`, but you can give it another name """


def hex_to_rgb(value):
    """ Return (red, green, blue) in float between 0-1 for the color given as #rrggbb. """
    value = value.lstrip('#')
    lv = len(value)
    rgb = tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    rgb = (rgb[0]/255, rgb[1]/255, rgb[2]/255)
    return rgb


def colorize_pdf(folder, in_file, out_file, color):
    er = None
    try:
        with open(os.path.join(folder, in_file), "rb") as f:
            source = PyPDF2.PdfFileReader(f, "rb")
            output = PyPDF2.PdfFileWriter()
            for page in range(source.getNumPages()):
                page = source.getPage(page)
                content_object = page["/Contents"].getObject()
                content = PyPDF2.pdf.ContentStream(content_object, source)
                i = 0
                for operands, operator in content.operations:
                    if operator == PyPDF2.utils.b_("rg") or operator == PyPDF2.utils.b_("RG"):
                        if operands == [0, 0, 0]:
                            content.operations[i][0]
                            content.operations[i] = ([PyPDF2.generic.FloatObject(color[0]),
                                                     PyPDF2.generic.FloatObject(color[1]),
                                                     PyPDF2.generic.FloatObject(color[2])],
                                                     content.operations[i][1])
                    i = i+1
                page.__setitem__(PyPDF2.generic.NameObject('/Contents'), content)
                output.addPage(page)
            try:
                with open(os.path.join(folder, out_file), "wb") as outputStream:
                    output.write(outputStream)
            except (IOError, ValueError, EOFError) as e:
                er = str(e)
            if er:
                raise KiPlotConfigurationError('Error creating `{}` ({})'.format(out_file, er))
    except (IOError, ValueError, EOFError) as e:
        er = str(e)
    if er:
        raise KiPlotConfigurationError('Error reading `{}` ({})'.format(in_file, er))


def merge_pdf(input_folder, input_files, output_folder, output_file):
    """ Merge all pages into one """
    output = PyPDF2.PdfFileWriter()
    # Collect all pages, as a merged one
    i = 0
    er = None
    open_files = []
    for filename in input_files:
        try:
            file = open(os.path.join(input_folder, filename), 'rb')
            open_files.append(file)
            pdf_reader = PyPDF2.PdfFileReader(file)
            page_obj = pdf_reader.getPage(0)
            if(i == 0):
                merged_page = page_obj
            else:
                merged_page.mergePage(page_obj)
            i = i+1
        except (IOError, ValueError, EOFError) as e:
            er = str(e)
        if er:
            raise KiPlotConfigurationError('Error reading `{}` ({})'.format(filename, er))
    output.addPage(merged_page)
    # Write the result to a file
    pdf_output = None
    try:
        pdf_output = open(os.path.join(output_folder, output_file), 'wb')
        output.write(pdf_output)
    except (IOError, ValueError, EOFError) as e:
        er = str(e)
    finally:
        if pdf_output:
            pdf_output.close()
    if er:
        raise KiPlotConfigurationError('Error creating `{}` ({})'.format(output_file, er))
    # Close the input files
    for f in open_files:
        f.close()


def create_pdf_from_pages(input_folder, input_files, output_fn):
    output = PyPDF2.PdfFileWriter()
    # Collect all pages
    open_files = []
    er = None
    for filename in input_files:
        try:
            file = open(os.path.join(input_folder, filename), 'rb')
            open_files.append(file)
            pdf_reader = PyPDF2.PdfFileReader(file)
            page_obj = pdf_reader.getPage(0)
            page_obj.compressContentStreams()
            output.addPage(page_obj)
        except (IOError, ValueError, EOFError) as e:
            er = str(e)
        if er:
            raise KiPlotConfigurationError('Error reading `{}` ({})'.format(filename, er))
    # Write all pages to a file
    pdf_output = None
    try:
        pdf_output = open(output_fn, 'wb')
        output.write(pdf_output)
    except (IOError, ValueError, EOFError) as e:
        er = str(e)
    finally:
        if pdf_output:
            pdf_output.close()
    if er:
        raise KiPlotConfigurationError('Error creating `{}` ({})'.format(output_fn, er))
    # Close the files
    for f in open_files:
        f.close()


class LayerOptions(Layer):
    """ Data for a layer """
    def __init__(self):
        super().__init__()
        self._unkown_is_error = True
        with document:
            self.color = ""
            """ Color used for this layer """

    def config(self, parent):
        super().config(parent)
        self.validate_color('color')


class PagesOptions(Optionable):
    """ One page of the output document """
    def __init__(self):
        super().__init__()
        self._unkown_is_error = True
        with document:
            self.mirror = False
            """ Print mirrored (X axis inverted) """
            self.monochrome = False
            """ Print in black and white """
            self.sheet_reference_layer = ''
            """ Layer to plot the page frame """
            self.layers = LayerOptions
            """ [list(dict)] List of layers printed in this page. Order is important, the last goes on top """

    def config(self, parent):
        super().config(parent)
        if isinstance(self.layers, type):
            raise KiPlotConfigurationError("Missing `layers` list")
        self.layers = Layer.solve(self.layers)
        if self.sheet_reference_layer:
            # Layer name to layer ID
            layer = Layer()
            name = self.sheet_reference_layer
            layer.layer = self.sheet_reference_layer
            self.sheet_reference_layer = layer._get_layer_id_from_name()
            # Check this is one of the specified layers
            layer = next(filter(lambda x: x._id == self.sheet_reference_layer, self.layers), None)
            if layer is None:
                raise KiPlotConfigurationError("The layer selected for the sheet reference ({}) isn't in the list of layers".
                                               format(name))


class PCB_PrintOptions(VariantOptions):
    # Mappings to KiCad config values. They should be the same used in drill_marks.py
    _drill_marks_map = {'none': 0, 'small': 1, 'full': 2}

    def __init__(self):
        with document:
            self.output_name = None
            """ {output} """
            self.output = GS.def_global_output
            """ Filename for the output PDF (%i=assembly, %x=pdf)"""
            self.hide_excluded = False
            """ Hide components in the Fab layer that are marked as excluded by a variant """
            self.pages = PagesOptions
            """ [list(dict)] List of pages to include in the output document.
                Each page contains one or more layers of the PCB """
        super().__init__()
        self._expand_ext = 'pdf'
        self._expand_id = 'assembly'

#     @property
#     def drill_marks(self):
#         return self._drill_marks
#
#     @drill_marks.setter
#     def drill_marks(self, val):
#         if val not in self._drill_marks_map:
#             raise KiPlotConfigurationError("Unknown drill mark type: {}".format(val))
#         self._drill_marks = val

    def config(self, parent):
        super().config(parent)
        if isinstance(self.pages, type):
            raise KiPlotConfigurationError("Missing `pages` list")

        # self._drill_marks = PCB_PrintOptions._drill_marks_map[self._drill_marks]

    def filter_components(self):
        if not self._comps:
            return
        comps_hash = self.get_refs_hash()
        self.cross_modules(GS.board, comps_hash)
        self.remove_paste_and_glue(GS.board, comps_hash)
        if self.hide_excluded:
            self.remove_fab(GS.board, comps_hash)

    def unfilter_components(self):
        if not self._comps:
            return
        comps_hash = self.get_refs_hash()
        self.uncross_modules(GS.board, comps_hash)
        self.restore_paste_and_glue(GS.board, comps_hash)
        if self.hide_excluded:
            self.restore_fab(GS.board, comps_hash)

    def get_targets(self, out_dir):
        return [self._parent.expand_filename(out_dir, self.output)]

    def generate_output(self, output):
        temp_dir = mkdtemp(prefix='tmp-kibot-pcb_print-')
        logger.debug('- Temporal dir: {}'.format(temp_dir))
        # Plot options
        plot_controller = PLOT_CONTROLLER(GS.board)
        plot_options = plot_controller.GetPlotOptions()
        plot_options.SetOutputDirectory(temp_dir)
        # Set General Options:
        plot_options.SetPlotValue(True)
        plot_options.SetPlotReference(True)
        plot_options.SetPlotInvisibleText(False)
        plot_options.SetPlotViaOnMaskLayer(False)
        plot_options.SetExcludeEdgeLayer(True)
        # plot_options.SetPlotPadsOnSilkLayer(False);
        plot_options.SetUseAuxOrigin(False)
        plot_options.SetNegative(False)
        plot_options.SetScale(1.0)
        plot_options.SetAutoScale(False)
        # Generate the output
        pages = []
        for n, p in enumerate(self.pages):
            # 1) Plot all layers to individual PDF files (B&W)
            for la in p.layers:
                id = la._id
                logger.debug('- Plotting layer {} ({})'.format(la.layer, id))
                plot_options.SetPlotFrameRef(id == p.sheet_reference_layer)
                plot_options.SetMirror(p.mirror)
                if IsCopperLayer(id):  # Should probably do this on mask layers as well
                    plot_options.SetDrillMarksType(2)  # NO_DRILL_SHAPE = 0, SMALL_DRILL_SHAPE = 1, FULL_DRILL_SHAPE  = 2
                else:
                    plot_options.SetDrillMarksType(0)  # NO_DRILL_SHAPE = 0, SMALL_DRILL_SHAPE = 1, FULL_DRILL_SHAPE  = 2
                plot_controller.SetLayer(id)
                plot_controller.OpenPlotfile(la.suffix, PLOT_FORMAT_PDF, "Assembly")
                plot_controller.PlotLayer()
            plot_controller.ClosePlot()
            # 2) Apply the colors to the PDFs
            filelist = []
            for la in p.layers:
                in_file = GS.pcb_basename+"-"+la.suffix+".pdf"
                if la.color != "#000000":
                    out_file = GS.pcb_basename+"-"+la.suffix+"-colored.pdf"
                    logger.debug('- Giving color to {} -> {} ({})'.format(in_file, out_file, la.color))
                    colorize_pdf(temp_dir, in_file, out_file, hex_to_rgb(la.color))
                    filelist.append(out_file)
                else:
                    filelist.append(in_file)
            # 3) Stack all layers in one file
            assembly_file = GS.pcb_basename+"-"+str(n)+".pdf"
            logger.debug('- Merging layers to {}'.format(assembly_file))
            merge_pdf(temp_dir, filelist, temp_dir, assembly_file)
            pages.append(assembly_file)
        # Join all pages in one file
        logger.debug('- Creating output file {}'.format(output))
        create_pdf_from_pages(temp_dir, pages, output)
        # Remove the temporal files
        rmtree(temp_dir)

    def run(self, output):
        super().run(output)
        # self.set_title(self.title)
        self.filter_components()
        self.generate_output(output)
        self.unfilter_components()


@output_class
class PCB_Print(BaseOutput):  # noqa: F821
    """ PCB Print
        Prints the PCB using a mechanism that is more flexible than `pdf_pcb_print`. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = PCB_PrintOptions
            """ [dict] Options for the `pcb_print` output """
