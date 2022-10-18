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
"""
import os
import shlex
import subprocess
from tempfile import NamedTemporaryFile
# Here we import the whole module to make monkeypatch work
from .error import KiPlotConfigurationError
from .misc import (PCBDRAW_ERR, W_AMBLIST, PCB_MAT_COLORS, PCB_FINISH_COLORS, SOLDER_COLORS, SILK_COLORS,
                   W_PCBDRAW)
from .gs import GS
from .optionable import Optionable
from .out_base import VariantOptions
from .macros import macros, document, output_class  # noqa: F401
from . import log
from .PcbDraw.plot import (PcbPlotter, PlotPaste, PlotPlaceholders, PlotSubstrate, PlotVCuts, mm2ki, PlotComponents)
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
            """ [dict|None] Replacements for PCB references using components (lib:component) """
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
            self.vcuts = False
            """ Render V-CUTS on the Cmts.User layer """
            self.warnings = 'visible'
            """ [visible,all,none] Using visible only the warnings about components in the visible side are generated """
            self.dpi = 300
            """ [10,1200] Dots per inch (resolution) of the generated image """
            self.format = 'svg'
            """ *[svg,png,jpg,bmp] Output format. Only used if no `output` is specified """
            self.output = GS.def_global_output
            """ *Name for the generated file """
            self.margin = 0
            """ [0,100] Margin around the generated image [mm] """
            self.outline_width = 0.15
            """ [0,10] Width of the trace to draw the PCB border [mm].
                Note this also affects the drill holes """
            self.show_solderpaste = True
            """ Show the solder paste layers """
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
        # Highlight
        if isinstance(self.highlight, type):
            self.highlight = None
        # Filter
        if isinstance(self.show_components, type):
            self.show_components = None
        elif isinstance(self.show_components, str):
            if self.variant or self.dnf_filter:
                logger.warning(W_AMBLIST + 'Ambiguous list of components to show `{}` vs variant/filter'.
                               format(self.show_components))
            if self.show_components == 'none':
                self.show_components = None
            else:
                self.show_components = []

        # Remap
        # TODO: Better remap option, like - ref: xxx\nlib: xxxx\ncomponent: xxxx
        if isinstance(self.remap, type):
            self.remap = {}
        elif isinstance(self.remap, PcbDrawRemap):
            parsed_remap = {}
            for ref, v in self.remap._tree.items():
                if not isinstance(v, str):
                    raise KiPlotConfigurationError("Wrong PcbDraw remap, must be `ref: lib:component` ({}: {})".format(ref, v))
                lib_comp = v.split(':')
                if len(lib_comp) == 2:
                    parsed_remap[ref] = lib_comp
                else:
                    raise KiPlotConfigurationError("Wrong PcbDraw remap, must be `ref: lib:component` ({}: {})".format(ref, v))
            self.remap = parsed_remap
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

    def _create_style(self):
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{\n')
            first = True
            for k, v in self.style.items():
                if first:
                    first = False
                else:
                    f.write(',\n')
                if isinstance(v, str):
                    f.write('  "{}": "{}"'.format(k, v))
                elif isinstance(v, bool):
                    f.write('  "{}": {}'.format(k, str(v).lower()))
                else:
                    f.write('  "{}": {}'.format(k, v))
            f.write('\n}\n')
            f.close()
            return f.name

    def get_targets(self, out_dir):
        return [self._parent.expand_filename(out_dir, self.output)]

    def build_plot_components(self):
        remapping = self.remap

        def remapping_fun(ref, lib, name):
            if ref in remapping:
                remapped_lib, remapped_name = remapping[ref]
                if name.endswith('.back'):
                    return remapped_lib, remapped_name + '.back'
                else:
                    return remapped_lib, remapped_name
            return lib, name

        resistor_values = {}
        # TODO: Implement resistor_values_input and resistor_flip
#         for mapping in resistor_values_input:
#             key, value = tuple(mapping.split(":"))
#             resistor_values[key] = ResistorValue(value=value)
#         for ref in resistor_flip:
#             field = resistor_values.get(ref, ResistorValue())
#             field.flip_bands = True
#             resistor_values[ref] = field

        plot_components = PlotComponents(remapping=remapping_fun,
                                         resistor_values=resistor_values,
                                         no_warn_back=self.warnings == 'visible')

        if self._comps or self.show_components:
            comps = self.get_fitted_refs()
            if self.show_components:
                comps += self.show_components
            filter_set = set(comps)
            plot_components.filter = lambda ref: ref in filter_set

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
            plotter.margin = mm2ki(self.margin)
            # TODO: Pass it directly? If no: remove file?
            tmp_style = None
            if self.style:
                if isinstance(self.style, str):
                    plotter.resolve_style(self.style)
                else:
                    tmp_style = self._create_style()
                    plotter.resolve_style(tmp_style)
            plotter.plot_plan = [PlotSubstrate(drill_holes=not self.no_drillholes, outline_width=mm2ki(self.outline_width))]
            if self.show_solderpaste:
                plotter.plot_plan.append(PlotPaste())
            if self.vcuts:
                # TODO: Make layer configurable
                plotter.plot_plan.append(PlotVCuts(layer=41))
            # Two filtering mechanism: 1) Specified list and 2) KiBot filters and variants
            if self.show_components is not None or self._comps:
                plotter.plot_plan.append(self.build_plot_components())
            if self.placeholder:
                plotter.plot_plan.append(PlotPlaceholders())

            image = plotter.plot()
        # Most errors are reported as RuntimeError
        # When the PCB can't be loaded we get IOError
        # When the SVG contains errors we get SyntaxError
        except (RuntimeError, SyntaxError, IOError) as e:
            logger.error('PcbDraw error: '+str(e))
            exit(PCBDRAW_ERR)
        finally:
            if tmp_style:
                os.remove(tmp_style)

        save(image, save_output_name, self.dpi, format=save_output_format)
        # Do we need to convert the saved file?
        if self.convert_command is not None:
            cmd = [self.convert_command, save_output_name]
            if self.format == 'jpg':
                cmd += ['-quality', '85%']
            cmd.append(name)
            _run_command(cmd)
            os.remove(save_output_name)
        return


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
