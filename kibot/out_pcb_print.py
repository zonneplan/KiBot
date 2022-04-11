# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2022 Albin Dennevi
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://gitlab.com/dennevi/Board2Pdf/
# Note: Original code released as Public Domain
import os
import subprocess
from pcbnew import PLOT_CONTROLLER, PLOT_FORMAT_PDF, FromMM
from shutil import rmtree
from tempfile import mkdtemp
from .error import KiPlotConfigurationError
from .gs import GS
from .optionable import Optionable
from .out_base import VariantOptions
from .kicad.color_theme import load_color_theme
from .kicad.patch_svg import patch_svg_file
from .misc import CMD_PCBNEW_PRINT_LAYERS, URL_PCBNEW_PRINT_LAYERS, PDF_PCB_PRINT
from .kiplot import check_script, exec_with_retry, add_extra_options
from .macros import macros, document, output_class  # noqa: F401
from .layer import Layer, get_priority
from . import PyPDF2
from . import log

logger = log.get_logger()

# TODO:
# - SVG?


def _run_command(cmd):
    logger.debug('Executing: '+str(cmd))
    try:
        cmd_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        logger.error('Failed to run %s, error %d', cmd[0], e.returncode)
        if e.output:
            logger.debug('Output from command: '+e.output.decode())
        exit(PDF_PCB_PRINT)
    logger.debug('Output from command:\n'+cmd_output.decode())


def hex_to_rgb(value):
    """ Return (red, green, blue) in float between 0-1 for the color given as #rrggbb. """
    value = value.lstrip('#')
    rgb = tuple(int(value[i:i+2], 16) for i in range(0, 6, 2))
    rgb = (rgb[0]/255, rgb[1]/255, rgb[2]/255)
    alpha = int(value[6:], 16)/255 if len(value) == 8 else 1.0
    return rgb, alpha


def to_gray(color):
    avg = (color[0]+color[1]+color[2])/3
    return (avg, avg, avg)


def colorize_pdf(folder, in_file, out_file, color, black_holes):
    er = None
    pdf_color = [PyPDF2.generic.FloatObject(color[0]), PyPDF2.generic.FloatObject(color[1]),
                 PyPDF2.generic.FloatObject(color[2])]
    black_color = [PyPDF2.generic.FloatObject(0), PyPDF2.generic.FloatObject(0), PyPDF2.generic.FloatObject(0)]
    try:
        with open(os.path.join(folder, in_file), "rb") as f:
            source = PyPDF2.PdfFileReader(f, "rb")
            output = PyPDF2.PdfFileWriter()
            for page in range(source.getNumPages()):
                page = source.getPage(page)
                content_object = page["/Contents"].getObject()
                content = PyPDF2.pdf.ContentStream(content_object, source)
                for i, (operands, operator) in enumerate(content.operations):
                    if operator == b"rg" or operator == b"RG":
                        if operands == [0, 0, 0]:
                            # Replace black by the selected color
                            content.operations[i] = (pdf_color, operator)
                        elif black_holes and operands == [1, 1, 1]:
                            # Replace white by black
                            content.operations[i] = (black_color, operator)
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
    extra_debug = GS.debug_level >= 3
    for filename in input_files:
        if extra_debug:
            logger.debug("  - {}".format(filename))
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


def colorize_layer(suffix, color, monochrome, filelist, temp_dir, black_holes=False):
    in_file = GS.pcb_basename+"-"+suffix+".pdf"
    if color != "#000000":
        out_file = GS.pcb_basename+"-"+suffix+"-colored.pdf"
        logger.debug('- Giving color to {} -> {} ({})'.format(in_file, out_file, color))
        rgb, alpha = hex_to_rgb(color)
        color = rgb if not monochrome else to_gray(rgb)
        colorize_pdf(temp_dir, in_file, out_file, color, black_holes)
        filelist.append(out_file)
    else:
        filelist.append(in_file)


class LayerOptions(Layer):
    """ Data for a layer """
    def __init__(self):
        super().__init__()
        self._unkown_is_error = True
        with document:
            self.color = ""
            """ Color used for this layer """
            self.plot_footprint_refs = True
            """ Include the footprint references """
            self.plot_footprint_values = True
            """ Include the footprint values """
            self.force_plot_invisible_refs_vals = False
            """ Include references and values even when they are marked as invisible """

    def config(self, parent):
        super().config(parent)
        if self.color:
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
            """ Print in gray scale """
            self.scaling = 1.0
            """ Scale factor (0 means autoscaling)"""
            self.title = ''
            """ Text used to replace the sheet title. %VALUE expansions are allowed.
                If it starts with `+` the text is concatenated """
            self.sheet = 'Assembly'
            """ Text to use for the `sheet` in the title block """
            self.sheet_reference_color = ''
            """ Color to use for the frame and title block """
            self.line_width = 0.1
            """ [0.02,2] For objects without width [mm] (KiCad 5) """
            self.negative_plot = False
            """ Invert black and white. Only useful for a single layer """
            self.exclude_pads_from_silkscreen = False
            """ Do not plot the component pads in the silk screen (KiCad 5.x only) """
            self.tent_vias = True
            """ Cover the vias """
            self.black_holes = True
            """ Change the drill holes to be black instead of white """
            self.sort_layers = False
            """ Try to sort the layers in the same order that uses KiCad for printing """
            self.layers = LayerOptions
            """ [list(dict)] List of layers printed in this page. Order is important, the last goes on top """

    def config(self, parent):
        super().config(parent)
        if isinstance(self.layers, type):
            raise KiPlotConfigurationError("Missing `layers` list")
        # Fill the ID member for all the layers
        self.layers = Layer.solve(self.layers)
        if self.sort_layers:
            self.layers.sort(key=lambda x: get_priority(x._id), reverse=True)
        if self.sheet_reference_color:
            self.validate_color('sheet_reference_color')


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
            self._drill_marks = 'full'
            """ What to use to indicate the drill places, can be none, small or full (for real scale) """
            self.color_theme = '_builtin_classic'
            """ Selects the color theme. Only applies to KiCad 6.
                To use the KiCad 6 default colors select `_builtin_default`.
                Usually user colors are stored as `user`, but you can give it another name """
            self.plot_sheet_reference = True
            """ Include the title-block """
            self.pages = PagesOptions
            """ [list(dict)] List of pages to include in the output document.
                Each page contains one or more layers of the PCB """
            self.title = ''
            """ Text used to replace the sheet title. %VALUE expansions are allowed.
                If it starts with `+` the text is concatenated """
        super().__init__()
        self._expand_ext = 'pdf'
        self._expand_id = 'assembly'

    @property
    def drill_marks(self):
        return self._drill_marks

    @drill_marks.setter
    def drill_marks(self, val):
        if val not in self._drill_marks_map:
            raise KiPlotConfigurationError("Unknown drill mark type: {}".format(val))
        self._drill_marks = val

    def config(self, parent):
        super().config(parent)
        if isinstance(self.pages, type):
            raise KiPlotConfigurationError("Missing `pages` list")
        self._color_theme = load_color_theme(self.color_theme)
        if self._color_theme is None:
            raise KiPlotConfigurationError("Unable to load `{}` color theme".format(self.color_theme))
        # Assign a color if none was defined
        layer_id2color = self._color_theme.layer_id2color
        for p in self.pages:
            for la in p.layers:
                if not la.color:
                    if la._id in layer_id2color:
                        la.color = layer_id2color[la._id]
                    else:
                        la.color = "#000000"
        self._drill_marks = PCB_PrintOptions._drill_marks_map[self._drill_marks]

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

    def clear_edge_cuts(self):
        tmp_layer = GS.board.GetLayerID(GS.work_layer)
        edge = GS.board.GetLayerID('Edge.Cuts')
        moved = []
        for g in GS.board.GetDrawings():
            if g.GetLayer() == edge:
                g.SetLayer(tmp_layer)
                moved.append(g)
        for m in GS.get_modules():
            for gi in m.GraphicalItems():
                if gi.GetLayer() == edge:
                    gi.SetLayer(tmp_layer)
                    moved.append(gi)
        self.moved_items = moved
        self.edge_layer = edge

    def restore_edge_cuts(self):
        for g in self.moved_items:
            g.SetLayer(self.edge_layer)

    def plot_frame_ki6(self, pc, po, p):
        """ KiCad 6 can plot the frame because it loads the worksheet format """
        self.clear_edge_cuts()
        po.SetPlotFrameRef(True)
        po.SetScale(1.0)
        po.SetNegative(False)
        pc.SetLayer(self.edge_layer)
        pc.OpenPlotfile('frame', PLOT_FORMAT_PDF, p.sheet)
        pc.PlotLayer()
        self.restore_edge_cuts()

    def plot_frame_ki5(self, dir_name):
        """ KiCad 5 crashes if we try to print the frame.
            So we print a frame using pcbnew_do export.
            We use SVG output to then generate a vectorized PDF. """
        output = os.path.join(dir_name, GS.pcb_basename+"-frame.svg")
        check_script(CMD_PCBNEW_PRINT_LAYERS, URL_PCBNEW_PRINT_LAYERS, '1.6.7')
        # Move all the drawings away
        # KiCad 5 always prints Edge.Cuts, so we make it empty
        self.clear_edge_cuts()
        # Save the PCB
        pcb_name, pcb_dir = self.save_tmp_dir_board('pcb_print')
        # Restore the layer
        self.restore_edge_cuts()
        # Output file name
        cmd = [CMD_PCBNEW_PRINT_LAYERS, 'export', '--output_name', output, '--monochrome', '--svg',
               pcb_name, dir_name, 'Edge.Cuts']
        cmd, video_remove = add_extra_options(cmd)
        # Execute it
        ret = exec_with_retry(cmd)
        # Remove the temporal PCB
        logger.debug('Removing temporal PCB used for frame `{}`'.format(pcb_dir))
        rmtree(pcb_dir)
        if ret:
            logger.error(CMD_PCBNEW_PRINT_LAYERS+' returned %d', ret)
            exit(PDF_PCB_PRINT)
        if video_remove:
            video_name = os.path.join(self.expand_filename_pcb(GS.out_dir), 'pcbnew_export_screencast.ogv')
            if os.path.isfile(video_name):
                os.remove(video_name)
        patch_svg_file(output, remove_bkg=True)
        # Note: rsvg-convert uses 90 dpi but KiCad (and the docs I found) says SVG pt is 72 dpi
        cmd = ['rsvg-convert', '-d', '72', '-p', '72', '-f', 'pdf', '-o', output.replace('.svg', '.pdf'), output]
        _run_command(cmd)

    def generate_output(self, output):
        temp_dir = mkdtemp(prefix='tmp-kibot-pcb_print-')
        logger.debug('- Temporal dir: {}'.format(temp_dir))
        # Plot options
        pc = PLOT_CONTROLLER(GS.board)
        po = pc.GetPlotOptions()
        po.SetOutputDirectory(temp_dir)
        # Set General Options:
        po.SetExcludeEdgeLayer(True)   # We plot it separately
        po.SetUseAuxOrigin(False)
        po.SetAutoScale(False)
        po.SetDrillMarksType(self._drill_marks)
        # Generate the output
        pages = []
        for n, p in enumerate(self.pages):
            self.set_title(p.title if p.title else self.title)
            # 1) Plot all layers to individual PDF files (B&W)
            po.SetPlotFrameRef(False)   # We plot it separately
            po.SetMirror(p.mirror)
            po.SetScale(p.scaling)
            po.SetNegative(p.negative_plot)
            po.SetPlotViaOnMaskLayer(not p.tent_vias)
            if GS.ki5():
                po.SetLineWidth(FromMM(p.line_width))
                po.SetPlotPadsOnSilkLayer(not p.exclude_pads_from_silkscreen)
            for la in p.layers:
                id = la._id
                logger.debug('- Plotting layer {} ({})'.format(la.layer, id))
                po.SetPlotReference(la.plot_footprint_refs)
                po.SetPlotValue(la.plot_footprint_values)
                po.SetPlotInvisibleText(la.force_plot_invisible_refs_vals)
                pc.SetLayer(id)
                pc.OpenPlotfile(la.suffix, PLOT_FORMAT_PDF, p.sheet)
                pc.PlotLayer()
            # 2) Plot the frame using an empty layer and 1.0 scale
            if self.plot_sheet_reference:
                logger.debug('- Plotting the frame')
                if GS.ki6():
                    self.plot_frame_ki6(pc, po, p)
                else:
                    self.plot_frame_ki5(temp_dir)
            pc.ClosePlot()
            # 3) Apply the colors to the layer PDFs
            filelist = []
            for la in p.layers:
                colorize_layer(la.suffix, la.color, p.monochrome, filelist, temp_dir, p.black_holes)
            # 4) Apply color to the frame
            if self.plot_sheet_reference:
                color = p.sheet_reference_color if p.sheet_reference_color else self._color_theme.pcb_frame
                colorize_layer('frame', color, p.monochrome, filelist, temp_dir)
            # 5) Stack all layers in one file
            assembly_file = GS.pcb_basename+"-"+str(n)+".pdf"
            logger.debug('- Merging layers to {}'.format(assembly_file))
            merge_pdf(temp_dir, filelist, temp_dir, assembly_file)
            pages.append(assembly_file)
            self.restore_title()
        # Join all pages in one file
        logger.debug('- Creating output file {}'.format(output))
        create_pdf_from_pages(temp_dir, pages, output)
        # Remove the temporal files
        rmtree(temp_dir)

    def run(self, output):
        super().run(output)
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
