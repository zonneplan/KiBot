# -*- coding: utf-8 -*-
# Copyright (c) 2020-2022 Salvador E. Tropea
# Copyright (c) 2020-2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# TODO: Package resources
"""
Dependencies:
  - from: RSVG
    role: Create PNG, JPG and BMP images
  - from: ImageMagick
    role: Create JPG and BMP images
  - from: LXML
    role: mandatory
  - name: numpy
    python_module: true
    debian: python3-numpy
    arch: python-numpy
    downloader: python
    role: Automatically adjust SVG margin
"""
import os
import shlex
import subprocess
from tempfile import NamedTemporaryFile
# Here we import the whole module to make monkeypatch work
from .error import KiPlotConfigurationError
from .misc import (PCBDRAW_ERR, PCB_MAT_COLORS, PCB_FINISH_COLORS, SOLDER_COLORS, SILK_COLORS, W_PCBDRAW)
from .gs import GS
from .layer import Layer
from .optionable import Optionable
from .out_base import VariantOptions
from .macros import macros, document, output_class  # noqa: F401
from . import log
from .PcbDraw.plot import (PcbPlotter, PlotPaste, PlotPlaceholders, PlotSubstrate, PlotVCuts, mm2ki, PlotComponents,
                           ResistorValue)
from .PcbDraw.convert import save


logger = log.get_logger()


def pcbdraw_warnings(tag, msg):
    logger.warning('{}({}) {}'.format(W_PCBDRAW, tag, msg))


def _get_tmp_name(ext):
    with NamedTemporaryFile(mode='w', suffix=ext, delete=False) as f:
        f.close()
    return f.name


def _run_command(cmd):
    logger.debug('Executing: '+shlex.join(cmd))
    try:
        cmd_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        logger.error('Failed to run %s, error %d', cmd[0], e.returncode)
        if e.output:
            logger.debug('Output from command: '+e.output.decode())
        exit(PCBDRAW_ERR)
    out = cmd_output.decode()
    if out.strip():
        logger.debug('Output from command:\n'+out)


class PcbDrawStyle(Optionable):
    def __init__(self):
        super().__init__()
        with document:
            self.copper = "#285e3a"
            """ *Color for the copper zones (covered by solder mask) """
            self.board = "#208b47"
            """ *Color for the board without copper (covered by solder mask) """
            self.silk = "#d5dce4"
            """ *Color for the silk screen """
            self.pads = "#8b898c"
            """ *Color for the exposed pads (metal finish) """
            self.outline = "#000000"
            """ *Color for the outline """
            self.clad = "#cabb3e"
            """ *Color for the PCB core (not covered by solder mask) """
            self.vcut = "#bf2600"
            """ Color for the V-CUTS """
            self.highlight_on_top = False
            """ Highlight over the component (not under) """
            self.highlight_style = "stroke:none;fill:#ff0000;opacity:0.5;"
            """ SVG code for the highlight style """
            self.highlight_padding = 1.5
            """ [0,1000] How much the highlight extends around the component [mm] """

    def config(self, parent):
        # Apply global defaults
        # PCB Material
        if GS.global_pcb_material is not None:
            material = GS.global_pcb_material.lower()
            for mat, color in PCB_MAT_COLORS.items():
                if mat in material:
                    self.clad = "#"+color
                    break
        # Solder mask
        if parent.bottom:
            name = GS.global_solder_mask_color_bottom or GS.global_solder_mask_color
        else:
            name = GS.global_solder_mask_color_top or GS.global_solder_mask_color
        if name and name.lower() in SOLDER_COLORS:
            (self.copper, self.board) = SOLDER_COLORS[name.lower()]
        # Silk screen
        if parent.bottom:
            name = GS.global_silk_screen_color_bottom or GS.global_silk_screen_color
        else:
            name = GS.global_silk_screen_color_top or GS.global_silk_screen_color
        if name and name.lower() in SILK_COLORS:
            self.silk = "#"+SILK_COLORS[name.lower()]
        # PCB Finish
        if GS.global_pcb_finish is not None:
            name = GS.global_pcb_finish.lower()
            for nm, color in PCB_FINISH_COLORS.items():
                if nm in name:
                    self.pads = "#"+color
                    break
        super().config(parent)
        self.validate_colors(['board', 'copper', 'board', 'silk', 'pads', 'outline', 'clad', 'vcut'])
        # Not implemented but required
        self.highlight_offset = 0

    def to_dict(self):
        return {k.replace('_', '-'): v for k, v in self.get_attrs_gen()}


class PcbDrawRemap(Optionable):
    """ This class accepts a free form dict.
        No validation is done. """
    def __init__(self):
        super().__init__()

    def config(self, parent):
        pass


class PcbDrawResistorRemap(Optionable):
    """ Reference -> New value """
    def __init__(self):
        super().__init__()
        with document:
            self.ref = ''
            """ *Reference for the resistor to change """
            self.reference = None
            """ {ref} """
            self.val = ''
            """ *Value to use for `ref` """
            self.value = None
            """ {val} """

    def config(self, parent):
        super().config(parent)
        if not self.ref or not self.val:
            raise KiPlotConfigurationError("The resistors remapping must specify a `ref` and a `val`")


class PcbDrawRemapComponents(Optionable):
    """ Reference -> Library + Footprint """
    def __init__(self):
        super().__init__()
        with document:
            self.ref = ''
            """ *Reference for the component to change """
            self.reference = None
            """ {ref} """
            self.lib = ''
            """ *Library to use """
            self.library = None
            """ {lib} """
            self.comp = ''
            """ *Component to use (from `lib`) """
            self.component = None
            """ {comp} """

    def config(self, parent):
        super().config(parent)
        if not self.ref or not self.lib or not self.comp:
            raise KiPlotConfigurationError("The component remapping must specify a `ref`, a `lib` and a `comp`")


class PcbDrawMargin(Optionable):
    """ To adjust each margin """
    def __init__(self):
        super().__init__()
        with document:
            self.left = 0
            """ Left margin [mm] """
            self.right = 0
            """ Right margin [mm] """
            self.top = 0
            """ Top margin [mm] """
            self.bottom = 0
            """ Bottom margin [mm] """


class PcbDrawOptions(VariantOptions):
    def __init__(self):
        with document:
            self.style = PcbDrawStyle
            """ *[string|dict] PCB style (colors). An internal name, the name of a JSON file or the style options """
            self.libs = Optionable
            """ [list(string)=[]] List of libraries """
            self.placeholder = False
            """ Show placeholder for missing components """
            self.remap = PcbDrawRemap
            """ [dict|None] (DEPRECATED) Replacements for PCB references using specified components (lib:component).
                Use `remap_components` instead """
            self.remap_components = PcbDrawRemapComponents
            """ [list(dict)] Replacements for PCB references using specified components.
                Replaces `remap` with type check """
            self.no_drillholes = False
            """ Do not make holes transparent """
            self.bottom = False
            """ *Render the bottom side of the board (default is top side) """
            self.mirror = False
            """ *Mirror the board """
            self.highlight = Optionable
            """ [list(string)=[]] List of components to highlight """
            self.show_components = Optionable
            """ *[list(string)|string=none] [none,all] List of components to draw, can be also a string for none or all.
                The default is none. IMPORTANT! This option is relevant only when no filters or variants are applied """
            self.add_to_variant = True
            """ The `show_components` list is added to the list of components indicated by the variant (fitted and not
                excluded).
                This is the old behavior, but isn't intuitive because the `show_components` meaning changes when a variant
                is used.
                To get a more coherent behavior disable this option, and `none` will always be `none`.
                Also `all` will be what the variant says """
            self.vcuts = False
            """ Render V-CUTS on the `vcuts_layer` layer """
            self.vcuts_layer = 'Cmts.User'
            """ Layer to render the V-CUTS, only used when `vcuts` is enabled.
                Note that any other content from this layer will be included """
            self.warnings = 'visible'
            """ [visible,all,none] Using visible only the warnings about components in the visible side are generated """
            self.dpi = 300
            """ [10,1200] Dots per inch (resolution) of the generated image """
            self.format = 'svg'
            """ *[svg,png,jpg,bmp] Output format. Only used if no `output` is specified """
            self.output = GS.def_global_output
            """ *Name for the generated file """
            self.margin = PcbDrawMargin
            """ [number|dict] Margin around the generated image [mm] """
            self.outline_width = 0.15
            """ [0,10] Width of the trace to draw the PCB border [mm].
                Note this also affects the drill holes """
            self.show_solderpaste = True
            """ Show the solder paste layers """
            self.resistor_remap = PcbDrawResistorRemap
            """ [list(dict)] List of resitors to be remapped. You can change the value of the resistors here """
            self.resistor_flip = Optionable
            """ [string|list(string)=''] List of resistors to flip its bands """
            self.size_detection = 'kicad_edge'
            """ [kicad_edge,kicad_all,svg_paths] Method used to detect the size of the resulting image.
                The `kicad_edge` method uses the size of the board as reported by KiCad,
                components that extend beyond the PCB limit will be cropped. You can manually
                adjust the margins to make them visible.
                The `kicad_all` method uses the whole size reported by KiCad. Usually includes extra space.
                The `svg_paths` uses all visible drawings in the image. To use this method you
                must install the `numpy` Python module (may not be available in docker images) """
        super().__init__()

    def config(self, parent):
        # Pre-parse the bottom option
        if 'bottom' in self._tree:
            bot = self._tree['bottom']
            if isinstance(bot, bool):
                self.bottom = bot
        super().config(parent)
        # Libs
        if isinstance(self.libs, type):
            self.libs = ['KiCAD-base']
        else:
            self.libs = ','.join(self.libs)
        # V-CUTS layer
        self._vcuts_layer = Layer.solve(self.vcuts_layer)[0]._id if self.vcuts else 41
        # Highlight
        if isinstance(self.highlight, type):
            self.highlight = None
        # Margin
        if isinstance(self.margin, type):
            self.margin = (0, 0, 0, 0)
        elif isinstance(self.margin, PcbDrawMargin):
            self.margin = (mm2ki(self.margin.left), mm2ki(self.margin.right),
                           mm2ki(self.margin.top), mm2ki(self.margin.bottom))
        else:
            margin = mm2ki(self.margin)
            self.margin = (margin, margin, margin, margin)
        # Filter
        if isinstance(self.show_components, type):
            # Default option is 'none'
            self.show_components = None
        elif isinstance(self.show_components, str):
            if self.show_components == 'none':
                self.show_components = None
            else:
                # Empty list: means we don't filter
                self.show_components = []
        # Resistors remap/flip
        if isinstance(self.resistor_remap, type):
            self.resistor_remap = []
        self.resistor_flip = Optionable.force_list(self.resistor_flip)
        # Remap
        self._remap = {}
        if isinstance(self.remap, PcbDrawRemap):
            for ref, v in self.remap._tree.items():
                if not isinstance(v, str):
                    raise KiPlotConfigurationError("Wrong PcbDraw remap, must be `ref: lib:component` ({}: {})".format(ref, v))
                lib_comp = v.split(':')
                if len(lib_comp) == 2:
                    self._remap[ref] = tuple(lib_comp)
                else:
                    raise KiPlotConfigurationError("Wrong PcbDraw remap, must be `ref: lib:component` ({}: {})".format(ref, v))
        if isinstance(self.remap_components, list):
            for mapping in self.remap_components:
                self._remap[mapping.ref] = (mapping.lib, mapping.comp)
        # Style
        if isinstance(self.style, type):
            # Apply the global defaults
            style = PcbDrawStyle()
            style.config(self)
            self.style = style.to_dict()
        elif isinstance(self.style, PcbDrawStyle):
            self.style = self.style.to_dict()
        self._expand_id = 'bottom' if self.bottom else 'top'
        self._expand_ext = self.format

    def get_targets(self, out_dir):
        return [self._parent.expand_filename(out_dir, self.output)]

    def build_plot_components(self):
        remapping = self._remap

        def remapping_fun(ref, lib, name):
            if ref in remapping:
                remapped_lib, remapped_name = remapping[ref]
                if name.endswith('.back'):
                    return remapped_lib, remapped_name + '.back'
                else:
                    return remapped_lib, remapped_name
            return lib, name

        resistor_values = {}
        for mapping in self.resistor_remap:
            resistor_values[mapping.ref] = ResistorValue(value=mapping.val)
        for ref in self.resistor_flip:
            field = resistor_values.get(ref, ResistorValue())
            field.flip_bands = True
            resistor_values[ref] = field

        plot_components = PlotComponents(remapping=remapping_fun,
                                         resistor_values=resistor_values,
                                         no_warn_back=self.warnings == 'visible')

        filter_set = None
        if self._comps:
            # A variant is applied, filter the DNF components
            all_comps = set(self.get_fitted_refs())
            if self.add_to_variant:
                # Old behavior
                all_comps.update(self.show_components)
                filter_set = all_comps
            else:
                # Something more coherent
                if self.show_components:
                    # The user supplied a list of components
                    # Use only the valid ones, but only if fitted
                    filter_set = set(self.show_components).intersection(all_comps)
                else:
                    # Empty list means all, but here is all fitted
                    filter_set = all_comps
        else:
            # No variant applied
            if self.show_components:
                # The user supplied a list of components
                # Note: if the list is empty this means we don't filter
                filter_set = set(self.show_components)
        if filter_set is not None:
            logger.debug('List of filtered components: '+str(filter_set))
            plot_components.filter = lambda ref: ref in filter_set
        else:
            logger.debug('Using all components')

        if self.highlight is not None:
            highlight_set = set(self.highlight)
            plot_components.highlight = lambda ref: ref in highlight_set
        return plot_components

    def run(self, name):
        super().run(name)
        # Select a name and format that PcbDraw can handle
        save_output_name = name
        save_output_format = self.format
        self.convert_command = None
        # Check we have the tools needed for the output format
        if self.format != 'svg':
            # We need RSVG for anything other than SVG
            self.ensure_tool('RSVG')
            # We need ImageMagick for anything other than SVG and PNG
            if self.format != 'png':
                self.convert_command = self.ensure_tool('ImageMagick')
                save_output_name = _get_tmp_name('.png')
                save_output_format = 'png'

        # Apply any variant
        self.filter_pcb_components(GS.board, do_3D=True)

        try:
            plotter = PcbPlotter(GS.board)
            # TODO: Review the paths, most probably add the system KiBot dir
            # Read libs from current dir
            # plotter.setup_arbitrary_data_path(".")
            # Libs indicated by PCBDRAW_LIB_PATH
            plotter.setup_env_data_path()
            # Libs from resources relative to the script
            plotter.setup_builtin_data_path()
            # Libs from the user HOME and the system
            plotter.setup_global_data_path()
            plotter.yield_warning = pcbdraw_warnings
            plotter.libs = self.libs
            plotter.render_back = self.bottom
            plotter.mirror = self.mirror
            plotter.margin = self.margin
            if self.style:
                if isinstance(self.style, str):
                    plotter.resolve_style(self.style)
                else:
                    plotter.style = self.style
            plotter.plot_plan = [PlotSubstrate(drill_holes=not self.no_drillholes, outline_width=mm2ki(self.outline_width))]
            if self.show_solderpaste:
                plotter.plot_plan.append(PlotPaste())
            if self.vcuts:
                plotter.plot_plan.append(PlotVCuts(layer=self._vcuts_layer))
            # Adjust the show_components option if needed
            if self.add_to_variant:
                # Enable the old behavior
                if self._comps and self.show_components is None:
                    # A variant automatically adds their components
                    # So `none` becomes `all`
                    self.show_components = []
            if self.show_components is not None:
                plotter.plot_plan.append(self.build_plot_components())
            if self.placeholder:
                plotter.plot_plan.append(PlotPlaceholders())
            plotter.compute_bbox = self.size_detection == 'svg_paths'
            # Make sure we can use svgpathtools
            if plotter.compute_bbox:
                self.ensure_tool('numpy')
            plotter.kicad_bb_only_edge = self.size_detection == 'kicad_edge'

            image = plotter.plot()
        # Most errors are reported as RuntimeError
        # When the PCB can't be loaded we get IOError
        # When the SVG contains errors we get SyntaxError
        except (RuntimeError, SyntaxError, IOError) as e:
            logger.error('PcbDraw error: '+str(e))
            exit(PCBDRAW_ERR)

        # Save the result
        logger.debug('Saving output to '+save_output_name)
        save(image, save_output_name, self.dpi, format=save_output_format)
        # Do we need to convert the saved file?
        if self.convert_command is not None:
            cmd = [self.convert_command, save_output_name]
            if self.format == 'jpg':
                cmd += ['-quality', '85%']
            cmd.append(name)
            _run_command(cmd)
            os.remove(save_output_name)

        # Undo the variant
        self.unfilter_pcb_components(GS.board, do_3D=True)


@output_class
class PcbDraw(BaseOutput):  # noqa: F821
    """ PcbDraw - Beautiful 2D PCB render
        Exports the PCB as a 2D model (SVG, PNG or JPG).
        Uses configurable colors.
        Can also render the components if the 2D models are available """
    def __init__(self):
        super().__init__()
        with document:
            self.options = PcbDrawOptions
            """ *[dict] Options for the `pcbdraw` output """
        self._category = 'PCB/docs'

    def get_dependencies(self):
        files = super().get_dependencies()
        if isinstance(self.options.style, str) and os.path.isfile(self.options.style):
            files.append(self.options.style)
        return files

    @staticmethod
    def get_conf_examples(name, layers, templates):
        outs = []
        for la in layers:
            is_top = la.is_top()
            is_bottom = la.is_bottom()
            if not is_top and not is_bottom:
                continue
            id = 'top' if is_top else 'bottom'
            for style in ['jlcpcb-green-enig', 'set-blue-enig', 'set-red-hasl']:
                style_2 = style.replace('-', '_')
                for fmt in ['svg', 'png', 'jpg']:
                    gb = {}
                    gb['name'] = 'basic_{}_{}_{}_{}'.format(name, fmt, style_2, id)
                    gb['comment'] = 'PCB 2D render in {} format, using {} style'.format(fmt.upper(), style)
                    gb['type'] = name
                    gb['dir'] = os.path.join('PCB', '2D_render', style_2)
                    ops = {'style': style, 'format': fmt}
                    if is_bottom:
                        ops['bottom'] = True
                    gb['options'] = ops
                    outs.append(gb)
        return outs
