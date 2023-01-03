# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023 Salvador E. Tropea
# Copyright (c) 2022-2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - from: KiKit
    role: mandatory
"""
import collections
from copy import deepcopy
import os
import re
import json
from tempfile import NamedTemporaryFile
from .error import KiPlotConfigurationError
from .gs import GS
from .kiplot import run_command, config_output
from .layer import Layer
from .misc import W_PANELEMPTY, KIKIT_UNIT_ALIASES
from .optionable import PanelOptions
from .out_base import VariantOptions
from .registrable import RegOutput
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


def update_dict(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update_dict(d.get(k, {}), v)
        elif isinstance(v, list) and k in d:
            d[k] = v+d[k]
        else:
            d[k] = v
    return d


class PanelOptionsWithPlugin(PanelOptions):
    def __init__(self):
        with document:
            self.code = ''
            """ Plugin specification (PACKAGE.FUNCTION or PYTHON_FILE.FUNCTION). Used for *plugin* """
            self.arg = ''
            """ Argument to pass to the plugin. Used for *plugin* """
        super().__init__()


class PanelizePage(PanelOptions):
    def __init__(self):
        with document:
            self.type = 'inherit'
            """ *[inherit,custom,A0,A1,A2,A3,A4,A5,A,B,C,D,E,USLetter,USLegal,USLedger,A0-portrait,A1-portrait,A2-portrait,
                 A3-portrait,A4-portrait,A5-portrait,A-portrait,B-portrait,C-portrait,D-portrait,E-portrait,
                 USLetter-portrait,USLegal-portrait,USLedger-portrait] Paper size. The default `inherit` option inherits
                 paper size from the source board. This feature is not supported on KiCAD 5 """
            self.page_size = None
            """ {type} """
            self.size = None
            """ {type} """
            self.anchor = 'tl'
            """ [tl,tr,bl,br,mt,mb,ml,mr,c] Point of the panel to be placed at given position. Can be one of tl, tr, bl, br
                (corners), mt, mb, ml, mr (middle of sides), c (center). The anchors refer to the panel outline """
            self.posx = 15
            """ [number|string] The X position of the panel on the page """
            self.pos_x = None
            """ {posx} """
            self.posy = 15
            """ [number|string] The Y position of the panel on the page """
            self.pos_y = None
            """ {posy} """
            self.width = 297
            """ [number|string] Width for the `custom` paper size """
            self.height = 210
            """ [number|string] Height for the `custom` paper size """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        self.add_units(('posx', 'posy', 'width', 'height'))


class PanelizeLayout(PanelOptionsWithPlugin):
    def __init__(self):
        with document:
            self.type = 'grid'
            """ [grid,plugin] In the plugin type only `code` and `arg` are relevant """
            self.hspace = 0
            """ [number|string] Specify the horizontal gap between the boards """
            self.vspace = 0
            """ [number|string] Specify the vertical gap between the boards """
            self.space = None
            """ [number|string] Specify the gap between the boards, overwrites `hspace` and `vspace` """
            self.rotation = 0
            """ [number|string] Rotate the boards before placing them in the panel """
            self.renamenet = 'Board_{n}-{orig}'
            """ A pattern by which to rename the nets. You can use {n} and {orig} to get the board number and original name """
            self.rename_net = None
            """ {renamenet} """
            self.renameref = '{orig}'
            """ A pattern by which to rename the references. You can use {n} and {orig} to get the board number and original
                name """
            self.rename_ref = None
            """ {renameref} """
            self.baketext = True
            """ A flag that indicates if text variables should be substituted or not """
            self.bake_text = None
            """ {baketext} """
            self.rows = 1
            """ *Specify the number of rows of boards in the grid pattern """
            self.cols = 1
            """ *Specify the number of columns of boards in the grid pattern """
            self.alternation = 'none'
            """ [none,rows,cols,rowsCols] Specify alternations of board rotation.
                none: Do not alternate.
                rows: Rotate boards by 180° on every next row.
                cols: Rotate boards by 180° on every next column.
                rowsCols: Rotate boards by 180° based on a chessboard pattern """
            self.vbackbone = 0
            """ [number|string] The width of vertical backbone (0 means no backbone). The backbone does not increase the
                spacing of the boards """
            self.hbackbone = 0
            """ [number|string] The width of horizontal backbone (0 means no backbone). The backbone does not increase the
                spacing of the boards """
            self.vboneskip = 0
            """ Skip every n vertical backbones. I.e., 1 means place only every other backbone """
            self.hboneskip = 0
            """ Skip every n horizontal backbones. I.e., 1 means place only every other backbone """
            self.vbonecut = True
            """ If there are both backbones specified, specifies if there should be a vertical cut where the backbones
                cross """
            self.hbonecut = True
            """ If there are both backbones specified, specifies if there should be a horizontal cut where the backbones
                cross """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        if self.space:
            self.hspace = self.vspace = self.space
        self.add_units(('vbackbone', 'hbackbone', 'hspace', 'vspace', 'space'))
        self.add_angle(('rotation', ))


class PanelizeTabs(PanelOptionsWithPlugin):
    def __init__(self):
        with document:
            self.type = 'spacing'
            """ *[fixed,spacing,full,annotation,plugin] Fixed: Place given number of tabs on the PCB edge.
                Spacing: Place tabs on the PCB edges based on spacing.
                Full: Create tabs that are full width of the PCB.
                Corner: Create tabs in the corners of the PCB.
                Annotation: Add tabs based on PCB annotations.
                Plugin: Uses an external python function, only `code` and `arg` are relevant """
            self.vwidth = 3
            """ [number|string] The width of tabs in the vertical direction. Used for *fixed* and *spacing* """
            self.hwidth = 3
            """ [number|string] The width of tabs in the horizontal direction. Used for *fixed* and *spacing* """
            self.width = None
            """ [number|string] The width of tabs in both directions. Overrides both `vwidth` and `hwidth`.
                Used for *fixed*, *spacing*, *corner* and *annotation* """
            self.vcount = 1
            """ Number of tabs in the vertical direction. Used for *fixed* """
            self.hcount = 1
            """ Number of tabs in the horizontal direction. Used for *fixed* """
            self.mindistance = 0
            """ [number|string] Minimal spacing between the tabs. If there are too many tabs, their count is reduced.
                Used for *fixed* """
            self.min_distance = None
            """ {mindistance} """
            self.spacing = 10
            """ [number|string] The maximum spacing of the tabs. Used for *spacing* """
            self.cutout = 1
            """ [number|string] When your design features open pockets on the side, this parameter specifies extra cutout depth in order to
                ensure that a sharp corner of the pocket can be milled. Used for *full* """
            self.tabfootprints = 'kikit:Tab'
            """ The footprint/s used for the *annotation* type. You can specify a list of footprints separated by comma """
            self.tab_footprints = None
            """ {tabfootprints} """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        if self.width:
            self.vwidth = self.hwidth = self.width
        self.add_units(('vwidth', 'hwidth', 'width', 'mindistance', 'spacing', 'cutout'))


class PanelizeCuts(PanelOptionsWithPlugin):
    def __init__(self):
        with document:
            self.type = 'none'
            """ *[none,mousebites,vcuts,layer,plugin] Layer: When KiKit reports it cannot perform cuts, you can render the cuts
                into a layer with this option to understand what's going on. Shouldn't be used for the final design """
            self.drill = 0.5
            """ [number|string] Drill size used for the *mousebites* """
            self.spacing = 0.8
            """ [number|string] The spacing of the holes used for the *mousebites* """
            self.offset = 0
            """ [number|string] Specify the *mousebites* and *vcuts* offset, positive offset puts the cuts into the board,
                negative puts the cuts into the tabs """
            self.prolong = 0
            """ [number|string] Distance for tangential prolongation of the cuts (to cut through the internal corner fillets
                caused by milling). Used for *mousebites* and *layer* """
            self.clearance = 0
            """ [number|string] Specify clearance for copper around V-cuts """
            self.cutcurves = False
            """ Specify if curves should be approximated by straight cuts (e.g., for cutting tabs on circular boards).
                Used for *vcuts* """
            self.cut_curves = None
            """ {cutcurves} """
            self.layer = 'Cmts.User'
            """ Specify the layer to render V-cuts on. Also used for the *layer* type """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        self.add_units(('drill', 'spacing', 'offset', 'prolong', 'clearance'))
        res = Layer.solve(self.layer)
        if len(res) > 1:
            raise KiPlotConfigurationError('Must select only one layer for the V-cuts ({})'.format(self.layer))


class PanelizeFraming(PanelOptionsWithPlugin):
    def __init__(self):
        with document:
            self.type = 'none'
            """ *[none,railstb,railslr,frame,tightframe,plugin] Railstb: Add rails on top and bottom.
            Railslr: Add rails on left and right.
            Frame: Add a frame around the board.
            Tighframe: Add a frame around the board which fills the whole area of the panel -
            the boards have just a milled slot around their perimeter.
            Plugin: Uses an external python function, only `code` and `arg` are relevant """
            self.hspace = 2
            """ [number|string] Specify the horizontal space between PCB and the frame/rail """
            self.vspace = 2
            """ [number|string] Specify the vertical space between PCB and the frame/rail """
            self.space = None
            """ [number|string] Specify the space between PCB and the frame/rail. Overrides `hspace` and `vspace` """
            self.width = 5
            """ [number|string] Specify with of the rails or frame """
            self.fillet = 0
            """ [number|string] Specify radius of fillet frame corners """
            self.chamfer = 0
            """ [number|string] Specify the size of chamfer frame corners """
            self.mintotalheight = 0
            """ [number|string] If needed, add extra material to the rail or frame to meet the minimal requested size.
                Useful for services that require minimal panel size """
            self.min_total_height = None
            """ {mintotalheight} """
            self.mintotalwidth = 0
            """ [number|string] If needed, add extra material to the rail or frame to meet the minimal requested size.
                Useful for services that require minimal panel size """
            self.min_total_width = None
            """ {mintotalwidth} """
            self.cuts = 'both'
            """ [none,both,v,h] Specify whether to add cuts to the corners of the frame for easy removal.
                Used for *frame* """
            self.slotwidth = 2
            """ [number|string] Width of the milled slot for *tightframe* """
            self.slot_width = None
            """ {slotwidth} """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        if self.space:
            self.hspace = self.vspace = self.space
        self.add_units(('hspace', 'vspace', 'space', 'width', 'fillet', 'chamfer', 'mintotalwidth', 'mintotalheight',
                        'slotwidth'))


class PanelizeTooling(PanelOptionsWithPlugin):
    def __init__(self):
        with document:
            self.type = 'none'
            """ *[none,3hole,4hole,plugin] Add none, 3 or 4 holes to the (rail/frame of) the panel """
            self.hoffset = 0
            """ [number|string] Horizontal offset from panel edges """
            self.voffset = 0
            """ [number|string] Vertical offset from panel edges """
            self.size = 1.152
            """ [number|string] Diameter of the holes """
            self.paste = False
            """ If True, the holes are included in the paste layer (therefore they appear on the stencil) """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        self.add_units(('hoffset', 'voffset', 'size'))


class PanelizeFiducials(PanelOptions):
    def __init__(self):
        with document:
            self.type = 'none'
            """ *[none,3fid,4fid,plugin] Add none, 3 or 4 fiducials to the (rail/frame of) the panel """
            self.hoffset = 0
            """ [number|string] Horizontal offset from panel edges """
            self.voffset = 0
            """ [number|string] Vertical offset from panel edges """
            self.coppersize = 1
            """ [number|string] Diameter of the copper spot """
            self.copper_size = None
            """ {coppersize} """
            self.opening = 1
            """ [number|string] Diameter of the solder mask opening """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        self.add_units(('hoffset', 'voffset', 'coppersize', 'opening'))


class PanelizeText(PanelOptions):
    def __init__(self):
        with document:
            self.type = 'none'
            """ *[none,simple] Currently fixed. BTW: don't ask me about this ridiculous default, is how KiKit works """
            self.text = ''
            """ *The text to be displayed. Note that you can escape ; via \\.
                Available variables in text: *date* formats current date as <year>-<month>-<day>,
                *time24* formats current time in 24-hour format,
                *boardTitle* the title from the source board,
                *boardDate* the date from the source board,
                *boardRevision* the revision from the source board,
                *boardCompany* the company from the source board,
                *boardComment1*-*boardComment9* comments from the source board """
            self.anchor = 'mt'
            """ [tl,tr,bl,br,mt,mb,ml,mr,c] Origin of the text. Can be one of tl, tr, bl, br (corners), mt, mb, ml, mr
                (middle of sides), c (center). The anchors refer to the panel outline """
            self.hoffset = 0
            """ [number|string] Specify the horizontal offset from anchor. Respects KiCAD coordinate system """
            self.voffset = 0
            """ [number|string] Specify the vertical offset from anchor. Respects KiCAD coordinate system """
            self.orientation = 0
            """ [number|string] Specify the orientation (angle) """
            self.width = 1.5
            """ [number|string] Width of the characters (the same parameters as KiCAD uses) """
            self.height = 1.5
            """ [number|string] Height of the characters (the same parameters as KiCAD uses) """
            self.hjustify = 'center'
            """ [left,right,center] Horizontal justification of the text """
            self.vjustify = 'center'
            """ [left,right,center] Vertical justification of the text """
            self.thickness = 0.3
            """ [number|string] Stroke thickness """
            self.layer = 'F.SilkS'
            """ Specify text layer """
            self.plugin = ''
            """ Specify the plugin that provides extra variables for the text """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        self.add_units(('hoffset', 'voffset', 'width', 'height', 'thickness'))
        self.add_angle(('orientation', ))
        res = Layer.solve(self.layer)
        if len(res) > 1:
            raise KiPlotConfigurationError('Must select only one layer for the text ({})'.format(self.layer))


class PanelizeCopperfill(PanelOptions):
    def __init__(self):
        with document:
            self.type = 'none'
            """ *[none,solid,hatched] How to fill non-board areas of the panel with copper """
            self.clearance = 0.5
            """ [number|string] Extra clearance from the board perimeters. Suitable for, e.g., not filling the tabs with
                copper """
            self.layers = 'F.Cu,B.Cu'
            """ [string|list(string)] List of layers to fill. Can be a comma-separated string.
                Using *all* means all external copper layers """
            self.width = 1
            """ [number|string] The width of the hatched strokes """
            self.spacing = 1
            """ [number|string] The space between the hatched strokes """
            self.orientation = 45
            """ [number|string] The orientation of the hatched strokes """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        self.add_units(('width', 'spacing', 'clearance'))
        self.add_angle(('orientation', ))
        if not isinstance(self.layers, str) or self.layers != 'all':
            if isinstance(self.layers, str):
                self.layers = self.layers.split(',')
            res = Layer.solve(self.layers)
            self.layers = ','.join([la.layer for la in res])


class PanelizePost(PanelOptions):
    def __init__(self):
        with document:
            self.type = 'auto'
            """ [auto] Currently fixed """
            self.copperfill = False
            """ Fill tabs and frame with copper (e.g., to save etchant or to increase rigidity of flex-PCB panels) """
            self.millradius = 0
            """ [number|string] Simulate the milling operation (add fillets to the internal corners).
                Specify mill radius (usually 1 mm). 0 radius disables the functionality """
            self.mill_radius = None
            """ {millradius} """
            self.reconstructarcs = False
            """ The panelization process works on top of a polygonal representation of the board.
                This options allows to reconstruct the arcs in the design before saving the panel """
            self.reconstruct_arcs = None
            """ {reconstructarcs} """
            self.refillzones = False
            """ Refill the user zones after the panel is build.
                This is only necessary when you want your zones to avoid cuts in panel """
            self.refill_zones = None
            """ {refillzones} """
            self.script = ''
            """ A path to custom Python file. The file should contain a function kikitPostprocess(panel, args) that
                receives the prepared panel as the kikit.panelize.Panel object and the user-supplied arguments as a
                string - see `scriptarg`. The function can make arbitrary changes to the panel - you can append text,
                footprints, alter labels, etc. The function is invoked after the whole panel is constructed
                (including all other postprocessing). If you try to add a functionality for a common fabrication
                houses via scripting, consider submitting PR for KiKit """
            self.scriptarg = ''
            """ An arbitrary string passed to the user post-processing script specified in script """
            self.script_arg = None
            """ {scriptarg} """
            self.origin = 'tl'
            """ [tl,tr,bl,br,mt,mb,ml,mr,c] Specify if the auxiliary origin an grid origin should be placed.
                Can be one of tl, tr, bl, br (corners), mt, mb, ml, mr (middle of sides), c (center).
                Empty string does not changes the origin """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        self.add_units(('millradius',))


class PanelizeDebug(PanelOptions):
    def __init__(self):
        with document:
            self.drawPartitionLines = False
            """ Draw partition lines """
            self.drawBackboneLines = False
            """ Draw backbone lines """
            self.drawboxes = False
            """ Draw boxes """
            self.trace = False
            """ Trace """
            self.deterministic = False
            """ Deterministic """
            self.drawtabfail = False
            """ Draw tab fail """
        super().__init__()


class PanelizeSource(PanelOptions):
    def __init__(self):
        with document:
            self.type = 'auto'
            """ *[auto,rectangle,annotation] How we select the area of the PCB tu used for the panelization.
                *auto* uses all the area reported by KiCad, *rectangle* a specified rectangle and
                *annotation* selects a contour marked by a kikit:Board footprint """
            self.stack = 'inherit'
            """ [inherit,2layer,4layer,6layer] Used to reduce the number of layers used for the panel """
            self.tolerance = 1
            """ [number|string] Extra space around the PCB reported size to be included. Used for *auto* and *annotation* """
            self.tlx = 0
            """ [number|string] Top left X coordinate of the rectangle used. Used for *rectangle* """
            self.tly = 0
            """ [number|string] Top left Y coordinate of the rectangle used. Used for *rectangle* """
            self.brx = 0
            """ [number|string] Bottom right X coordinate of the rectangle used. Used for *rectangle* """
            self.bry = 0
            """ [number|string] Bottom right Y coordinate of the rectangle used. Used for *rectangle* """
            self.ref = ''
            """ Reference for the kikit:Board footprint used to select the contour. Used for *annotation* """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        self.add_units(('tolerance', 'tlx', 'tly', 'brx', 'bry'))


class PanelizeConfig(PanelOptions):
    def __init__(self):
        with document:
            self.name = ''
            """ A name to identify this configuration. If empty will be the order in the list, starting with 1.
                Don't use just a number or it will be confused as an index """
            self.extends = ''
            """ A configuration to use as base for this one. Use the following format: `OUTPUT_NAME[CFG_NAME]` """
            self.page = PanelizePage
            """ *[dict] Sets page size on the resulting panel and position the panel in the page """
            self.layout = PanelizeLayout
            """ *[dict] Layout used for the panel """
            self.tabs = PanelizeTabs
            """ *[dict] Style of the tabs used to join the PCB copies """
            self.cuts = PanelizeCuts
            """ *[dict] Specify how to perform the cuts on the tabs separating the board """
            self.framing = PanelizeFraming
            """ *[dict] Specify the frame around the boards """
            self.tooling = PanelizeTooling
            """ *[dict] Used to add tooling holes to the (rail/frame of) the panel """
            self.fiducials = PanelizeFiducials
            """ *[dict] Used to add fiducial marks to the (rail/frame of) the panel """
            self.text = PanelizeText
            """ [dict] Used to add text to the panel """
            self.text2 = PanelizeText
            """ [dict] Used to add text to the panel """
            self.text3 = PanelizeText
            """ [dict] Used to add text to the panel """
            self.text4 = PanelizeText
            """ [dict] Used to add text to the panel """
            self.copperfill = PanelizeCopperfill
            """ [dict] Fill non-board areas of the panel with copper """
            self.post = PanelizePost
            """ [dict] Finishing touches to the panel """
            self.debug = PanelizeDebug
            """ [dict] Debug options """
            self.source = PanelizeSource
            """ [dict] Used to adjust details of which part of the PCB is panelized """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        # Avoid confusing names
        name_is_number = True
        try:
            _ = int(self.name)
        except ValueError:
            name_is_number = False
        if name_is_number:
            raise KiPlotConfigurationError("Don't use a number as name, this can be confused with an index ({})".
                                           format(self.name))
        # Make None all things not specified
        for k, v in self.get_attrs_gen():
            if isinstance(v, type):
                setattr(self, k, None)


class PanelizeOptions(VariantOptions):
    _extends_regex = re.compile(r'(.+)\[(.+)\]')

    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i=panel, %x=kicad_pcb) """
            self.configs = PanelizeConfig
            """ *[list(dict)|list(string)|string] One or more configurations used to create the panel.
                Use a string to include an external configuration, i.e. `myDefault.json`.
                You can also include a preset using `:name`, i.e. `:vcuts`.
                Use a dict to specify the options using the KiBot YAML file """
            self.title = ''
            """ Text used to replace the sheet title. %VALUE expansions are allowed.
                If it starts with `+` the text is concatenated """
            self.units = 'mm'
            """ [millimeters,inches,mils,mm,cm,dm,m,mil,inch,in] Units used when omitted """
            self.default_angles = 'deg'
            """ [deg,°,rad] Angles used when omitted """
            self.create_preview = False
            """ Use PcbDraw to create a preview of the panel """
        super().__init__()
        self._expand_id = 'panel'
        self._expand_ext = 'kicad_pcb'

    def solve_cfg_name(self, cfg):
        """ Find the name of a configuration that isn't yet configured """
        name = cfg.get('name')
        if name:
            return name
        return str(self._tree['configs'].index(cfg)+1)

    def solve_extends(self, tree, level=0, used=None, our_name=None):
        base = tree.get('extends')
        if our_name is None:
            our_name = '{}[{}]'.format(self._parent.name, self.solve_cfg_name(tree))
        if used is None:
            used = {our_name}
        else:
            if our_name in used:
                raise KiPlotConfigurationError('Recursive extends detected in `extends: {}` ({})'.format(base, used))
            used.add(our_name)
        logger.debugl(1, "Extending from "+base)
        # Should be an string
        if not isinstance(base, str):
            raise KiPlotConfigurationError('`extends` must be a string, not {}'.format(type(base)))
        # Extract the output and config names
        m = PanelizeOptions._extends_regex.match(base)
        if m is None:
            raise KiPlotConfigurationError('Malformed `extends` reference: `{}` use OUTPUT_NAME[CFG_NAME]'.format(base))
        out_name, cfg_name = m.groups()
        # Look for the output
        out = RegOutput.get_output(out_name)
        if out is None:
            raise KiPlotConfigurationError('Unknown output `{}` in `extends: {}`'.format(out_name, base))
        # Look for the config
        configs = None
        out_options = out._tree.get('options')
        if out_options:
            configs = out_options.get('configs')
        if configs is None or isinstance(configs, str):
            raise KiPlotConfigurationError("Using `extends: {}` but `{}` hasn't configs to copy". format(base, out_name))
        cfg_name_is_number = True
        try:
            id = int(cfg_name)-1
        except ValueError:
            cfg_name_is_number = False
        if cfg_name_is_number:
            # Using an index, is it valid?
            if id >= len(configs):
                raise KiPlotConfigurationError('Using `extends: {}` but `{}` has {} configs'.
                                               format(base, out_name, len(configs)))
            origin = configs[id]
        else:
            # Using a name
            origin = next(filter(lambda x: 'name' in x and x['name'] == cfg_name, configs), None)
            if origin is None:
                raise KiPlotConfigurationError("Using `extends: {}` but `{}` doesn't define `{}`".
                                               format(base, out_name, cfg_name))
        # Now we have the origin
        # Does it also use extends?
        origin_extends = origin.get('extends')
        if origin_extends:
            origin = self.solve_extends(origin, level=level+1, used=used, our_name=base)
        # Copy the origin, update it and replace the current values
        logger.debugl(1, "{} before applying {}: {}".format(our_name, base, tree))
        logger.debugl(1, "- Should add {}".format(origin))
        new_origin = deepcopy(origin)
        update_dict(new_origin, tree)
        if level:
            tree = deepcopy(tree)
        update_dict(tree, new_origin)
        if not level:
            # Remove the extends, we solved it
            del tree['extends']
        logger.debugl(1, "After apply: {}".format(tree))
        return tree

    def config(self, parent):
        self._parent = parent
        # Look for configs that uses extends
        configs = self._tree.get('configs')
        if configs:
            list(map(self.solve_extends, filter(lambda x: 'extends' in x, configs)))
        super().config(parent)
        self.units = KIKIT_UNIT_ALIASES.get(self.units, self.units)
        if isinstance(self.configs, type):
            logger.warning(W_PANELEMPTY+'Generating a panel with default options, not very useful')
            self.configs = []
        elif isinstance(self.configs, str):
            self.configs = [self.configs]
        for c, cfg in enumerate(self.configs):
            if not cfg.name:
                cfg.name = str(c+1)

    def create_config(self, cfg):
        with NamedTemporaryFile(mode='w', delete=False, suffix='.json', prefix='kibot_panel_cfg') as f:
            logger.debug('Writing panel config to '+f.name)
            cfg_d = {}
            for k, v in cfg.get_attrs_gen():
                if isinstance(v, PanelOptions):
                    cfg_d[k] = {ky: va for ky, va in v.get_attrs_gen() if va is not None and v.get_user_defined(ky)}
            js = json.dumps(cfg_d, indent=4)
            logger.debugl(1, js)
            f.write(js)
            return f.name

    def create_preview_file(self, name):
        if not self.create_preview or not os.path.isfile(name):
            return
        img_name = os.path.splitext(name)[0]+'.png'
        tree = {'name': '_temporal_pcbdraw_preview',
                'type': 'pcbdraw',
                'comment': 'Internally created for panel preview',
                'options': {'output': img_name, 'variant': '', 'format': 'png'}}
        out = RegOutput.get_class_for('pcbdraw')()
        out.set_tree(tree)
        config_output(out)
        logger.debug('Loading PCB panel ...')
        board = GS.load_board_low_level(name)
        logger.debug('Creating preview image ...')
        out.options.create_image(img_name, board)
        # KiCad loads the project automagically, so now we have the wrong project loaded
        # We need to unload the current project to load the new one
        # But we also need to reload the PCB, this is ridiculous ...
        GS.reload_project(GS.pro_file)

    def run(self, output):
        cmd_kikit, version = self.ensure_tool_get_ver('KiKit')
        if GS.ki5 and version >= (1, 1, 0):
            raise KiPlotConfigurationError("Installed KiKit doesn't support KiCad 5")
        super().run(output)
        fname = self.save_tmp_board_if_variant(new_title=self.title, do_3D=True)
        # Create the command
        cmd = [cmd_kikit, 'panelize']  # , '--dump', 'test.json'
        # Add all the configurations
        for cfg in self.configs:
            cmd.append('--preset')
            if isinstance(cfg, str):
                if cfg[0] != ':' and not os.path.isfile(cfg):
                    raise KiPlotConfigurationError('Missing config file: '+cfg)
                cmd.append(cfg)
            else:
                cfg_f = self.create_config(cfg)
                self._files_to_remove.append(cfg_f)
                cmd.append(cfg_f)
        # Add the PCB and output
        cmd.append(fname)
        cmd.append(output)
        try:
            run_command(cmd)
            self.create_preview_file(output)
        finally:
            self.remove_temporals()

    def get_targets(self, out_dir):
        pcb_name = self._parent.expand_filename(out_dir, self.output)
        files = [pcb_name]
        if self.create_preview:
            files.append(os.path.splitext(pcb_name)[0]+'.png')
        return files


@output_class
class Panelize(BaseOutput):  # noqa: F821
    """ Panelize
        Creates a panel to fabricate various copies of the PCB at once.
        It currently uses the KiKit tool, which must be available.
        Consult KiKit docs for detailed information.
        [KiKit panelization docs](https://github.com/yaqwsx/KiKit/blob/master/doc/examples.md).
        Current versions of KiKit only support KiCad 6 and my tests using
        KiKit 1.0.5 (the last to support KiCad 5) shown some
        incompatibilities.
        Note that you don't need to specify the units for all distances.
        If they are omitted they are assumed to be `units`.
        The same is valid for angles, using `default_angles` """
    def __init__(self):
        super().__init__()
        with document:
            self.options = PanelizeOptions
            """ *[dict] Options for the `Panelize` output """
        self._category = 'PCB/fabrication'

    @staticmethod
    def get_conf_examples(name, layers, templates):
        if not GS.check_tool(name, 'KiKit'):
            return None
        outs = []
        for tpl in templates:
            for out in tpl:
                if out['type'] == 'panelize':
                    outs.append(out)
        return outs
