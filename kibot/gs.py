# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
import re
import json
try:
    import pcbnew
except ImportError:
    # This is caught by __main__, ignore the error here
    class pcbnew(object):
        IU_PER_MM = 1
        IU_PER_MILS = 1
from datetime import datetime
from shutil import copy2
from sys import exit, exc_info
from traceback import extract_stack, format_list, print_tb
from .misc import EXIT_BAD_ARGS, W_DATEFORMAT, W_UNKVAR, WRONG_INSTALL, CORRUPTED_PRO
from .log import get_logger

logger = get_logger(__name__)
if hasattr(pcbnew, 'IU_PER_MM'):
    IU_PER_MM = pcbnew.IU_PER_MM
    IU_PER_MILS = pcbnew.IU_PER_MILS
else:
    IU_PER_MM = pcbnew.pcbIUScale.IU_PER_MM
    IU_PER_MILS = pcbnew.pcbIUScale.IU_PER_MILS
if hasattr(pcbnew, 'DRILL_MARKS_NO_DRILL_SHAPE'):
    NO_DRILL_SHAPE = pcbnew.DRILL_MARKS_NO_DRILL_SHAPE
    SMALL_DRILL_SHAPE = pcbnew.DRILL_MARKS_SMALL_DRILL_SHAPE
    FULL_DRILL_SHAPE = pcbnew.DRILL_MARKS_FULL_DRILL_SHAPE
elif hasattr(pcbnew, 'PCB_PLOT_PARAMS'):
    NO_DRILL_SHAPE = pcbnew.PCB_PLOT_PARAMS.NO_DRILL_SHAPE
    SMALL_DRILL_SHAPE = pcbnew.PCB_PLOT_PARAMS.SMALL_DRILL_SHAPE
    FULL_DRILL_SHAPE = pcbnew.PCB_PLOT_PARAMS.FULL_DRILL_SHAPE
# KiCad 6 uses IUs for SVGs, with option for SVG_Precision
# KiCad 5 uses a very different scale based on inches
# KiCad 7 uses mm
KICAD5_SVG_SCALE = 116930/297002200


class GS(object):
    """
    Class to keep the global settings.
    Is a static class, just a placeholder for some global variables.
    """
    # PCB name and useful parts
    pcb_file = None      # /.../dir/pcb.kicad_pcb
    pcb_no_ext = None    # /.../dir/pcb
    pcb_dir = None       # /.../dir
    pcb_basename = None  # pcb
    pcb_last_dir = None  # dir
    # SCH name and useful parts
    sch_file = None      # /.../dir/file.sch
    sch_no_ext = None    # /.../dir/file
    sch_dir = None       # /.../dir
    sch_last_dir = None  # dir
    sch_basename = None  # file
    # Project and useful parts
    pro_file = None      # /.../dir/file.kicad_pro (or .pro)
    pro_no_ext = None    # /.../dir/file
    pro_dir = None       # /.../dir
    pro_last_dir = None  # dir
    pro_basename = None  # file
    pro_ext = '.pro'
    pro_variables = None  # KiCad 6 text variables defined in the project
    vars_regex = re.compile(r'\$\{([^\}]+)\}')
    # Main output dir
    out_dir = None
    out_dir_in_cmd_line = False
    filter_file = None
    board = None
    sch = None
    debug_enabled = False
    debug_level = 0
    kibot_version = None
    n = datetime.now()
    on_windows = False
    kicad_version = ''
    kicad_conf_path = None
    kicad_share_path = None
    kicad_dir = 'kicad'
    kicad_plugins_dirs = []
    work_layer = 'Rescue'
    # KiCad version: major*1e6+minor*1e3+patch
    kicad_version_n = 0
    kicad_version_major = 0
    kicad_version_minor = 0
    kicad_version_patch = 0
    # Data from the SCH because it doesn't have a Python API
    sch_title = None
    sch_date = None
    sch_rev = None
    sch_comp = None
    sch_com = [None]*9
    # Data from the board title block
    pcb_title = None
    pcb_date = None
    pcb_rev = None
    pcb_comp = None
    pcb_com = [None]*9
    # Current variant/s
    variant = None
    # All the outputs
    outputs = None
    # Name for the output we are generating
    current_output = None
    test_boolean = True
    test_number = 5
    stackup = None
    # Preprocessor definitions
    cli_defines = {}
    kikit_units_to_kicad = {'mm': IU_PER_MM, 'cm': 10*IU_PER_MM, 'dm': 100*IU_PER_MM,
                            'm': 1000*IU_PER_MM, 'mil': IU_PER_MILS, 'inch': 1000*IU_PER_MILS,
                            'in': 1000*IU_PER_MILS}
    #
    # Global defaults
    #
    # Options from command line
    cli_global_defs = {}
    # The variant value, but already solved
    solved_global_variant = None
    #  This is used as default value for classes supporting "output" option
    def_global_output = '%f-%i%I%v.%x'
    # The class that controls the global options
    class_for_global_opts = None
    global_cache_3d_resistors = None
    global_castellated_pads = None
    global_colored_tht_resistors = None
    global_copper_thickness = None
    global_cross_footprints_for_dnp = None
    global_cross_no_body = None
    global_csv_accept_no_ref = None
    global_date_format = None
    global_date_time_format = None
    global_default_resistor_tolerance = None
    global_drc_exclusions_workaround = None
    global_dir = None
    global_disable_3d_alias_as_env = None
    global_drill_size_increment = None
    global_edge_connector = None
    global_edge_plating = None
    global_extra_pth_drill = None
    global_field_3D_model = None
    global_field_lcsc_part = None
    global_field_package = None
    global_field_power = None
    global_field_temp_coef = None
    global_field_tolerance = None
    global_field_voltage = None
    global_hide_excluded = None
    global_git_diff_strategy = None
    global_impedance_controlled = None
    global_invalidate_pcb_text_cache = None
    global_kiauto_time_out_scale = None
    global_kiauto_wait_start = None
    #  This value will overwrite GS.def_global_output if defined
    #  Classes supporting global "output" option must call super().__init__()
    #  after defining its own options to allow Optionable do the overwrite.
    global_output = None
    global_pcb_finish = None
    global_pcb_material = None
    global_remove_solder_paste_for_dnp = None
    global_remove_adhesive_for_dnp = None
    global_resources_dir = None
    global_restore_project = None
    global_set_text_variables_before_output = None
    global_silk_screen_color = None
    global_silk_screen_color_bottom = None
    global_silk_screen_color_top = None
    global_solder_mask_color = None
    global_solder_mask_color_bottom = None
    global_solder_mask_color_top = None
    global_time_format = None
    global_time_reformat = None
    global_units = None
    global_use_dir_for_preflights = None
    global_use_os_env_for_expand = None
    global_variant = None
    # Only for v7+
    global_allow_blind_buried_vias = None
    global_allow_microvias = None
    global_erc_grid = None
    global_kicad_dnp_applied = None
    global_kicad_dnp_applies_to_3D = None
    global_cross_using_kicad = None

    @staticmethod
    def set_sch(name):
        if name:
            name = os.path.abspath(name)
            GS.sch_file = name
            GS.sch_basename = os.path.splitext(os.path.basename(name))[0]
            GS.sch_no_ext = os.path.splitext(name)[0]
            GS.sch_dir = os.path.dirname(name)
            GS.sch_last_dir = os.path.basename(GS.sch_dir)

    @staticmethod
    def set_pcb(name):
        if name:
            name = os.path.abspath(name)
            GS.pcb_file = name
            GS.pcb_basename = os.path.splitext(os.path.basename(name))[0]
            GS.pcb_no_ext = os.path.splitext(name)[0]
            GS.pcb_dir = os.path.dirname(name)
            GS.pcb_last_dir = os.path.basename(GS.pcb_dir)

    @staticmethod
    def set_pro(name):
        if name:
            name = os.path.abspath(name)
            GS.pro_file = name
            GS.pro_basename = os.path.splitext(os.path.basename(name))[0]
            GS.pro_no_ext = os.path.splitext(name)[0]
            GS.pro_dir = os.path.dirname(name)
            GS.pro_last_dir = os.path.basename(GS.pro_dir)

    @staticmethod
    def load_pro_variables():
        if GS.pro_variables is not None:
            return GS.pro_variables
        if GS.pro_file is None or GS.pro_ext == '.pro':
            return {}
        # Get the text_variables
        with open(GS.pro_file, 'rt') as f:
            pro_text = f.read()
        try:
            data = json.loads(pro_text)
        except Exception:
            GS.exit_with_error('Corrupted project {}'.format(GS.pro_file), CORRUPTED_PRO)
        GS.pro_variables = data.get('text_variables', {})
        logger.debug("Current text variables: {}".format(GS.pro_variables))
        return GS.pro_variables

    @staticmethod
    def read_pro():
        if GS.pro_file:
            # Note: We use binary mode to preserve the original end of lines
            # Otherwise git could see changes in the file
            with open(GS.pro_file, 'rb') as f:
                return f.read()

    @staticmethod
    def write_pro(prj):
        if GS.pro_file and prj:
            with open(GS.pro_file, 'wb') as f:
                f.write(prj)

    @staticmethod
    def load_sch_title_block():
        if GS.sch_title is not None:
            return
        assert GS.sch is not None
        GS.sch_title = GS.sch.title
        GS.sch_date = GS.sch.date
        GS.sch_rev = GS.sch.revision
        GS.sch_comp = GS.sch.company
        GS.sch_com = GS.sch.comment

    @staticmethod
    def format_date(d, fname, what):
        if not d:
            return datetime.fromtimestamp(os.path.getmtime(fname)).strftime(GS.global_date_time_format)
        elif GS.global_time_reformat:
            try:
                dt = datetime.fromisoformat(d)
            except ValueError as e:
                logger.warning(W_DATEFORMAT+"Trying to reformat {} time, but not in ISO format ({})".format(what, d))
                logger.warning(W_DATEFORMAT+"Problem: {}".format(e))
                return d
            return dt.strftime(GS.global_date_format)
        return d

    @staticmethod
    def get_pcb_comment(title_block, num):
        if GS.ki6:
            # Backward compatibility ... what's this?
            # Also: Maintaining the same numbers used before (and found in the file) is asking too much?
            return title_block.GetComment(num)
        if num == 0:
            return title_block.GetComment1()
        if num == 1:
            return title_block.GetComment2()
        if num == 2:
            return title_block.GetComment3()
        if num == 3:
            return title_block.GetComment4()
        return ''

    @staticmethod
    def p2v_k7(point):
        """ KiCad v7 changed various wxPoint args to VECTOR2I.
            This helper changes the types accordingly """
        if GS.ki8:
            return pcbnew.VECTOR2I(point.x, point.y)
        elif GS.ki7:
            return pcbnew.VECTOR2I(point)
        return point

    @staticmethod
    def get_modules():
        if GS.ki6:
            return GS.board.GetFootprints()
        return GS.board.GetModules()

    @staticmethod
    def get_modules_board(board):
        if GS.ki6:
            return board.GetFootprints()
        return board.GetModules()

    @staticmethod
    def get_aux_origin():
        if GS.board is None:
            return (0, 0)
        if GS.ki6:
            settings = GS.board.GetDesignSettings()
            return settings.GetAuxOrigin()
        return GS.board.GetAuxOrigin()

    @staticmethod
    def get_center(m):
        if GS.ki5:
            return m.GetCenter()
        return m.GetPosition()

    @staticmethod
    def get_fp_size(m):
        if GS.ki5:
            pads = m.Pads()
            r = pcbnew.EDA_RECT()
            for pad in pads:
                r.Merge(pad.GetBoundingBox())
            rot = m.GetOrientationDegrees()
            if rot == 270 or rot == 90:
                return (r.GetHeight(), r.GetWidth())
            return (r.GetWidth(), r.GetHeight())
        # KiCad 6
        r = m.GetFpPadsLocalBbox()
        return (r.GetWidth(), r.GetHeight())

    @staticmethod
    def unit_name_to_scale_factor(units):
        if units == 'millimeters':
            return 1.0/IU_PER_MM
        if units == 'mils':
            return 1.0/IU_PER_MILS
        # Inches
        return 0.001/IU_PER_MILS

    @staticmethod
    def to_mm(val):
        return float(val)/IU_PER_MM

    @staticmethod
    def from_mm(val):
        return int(val*IU_PER_MM)

    @staticmethod
    def to_mils(val):
        return val/IU_PER_MILS

    @staticmethod
    def make_bkp(fname):
        bkp = fname+'-bak'
        os.replace(fname, bkp)

    @staticmethod
    def zones():
        return pcbnew.ZONES() if GS.ki6 else pcbnew.ZONE_CONTAINERS()

    @staticmethod
    def layers_contains(layers, id):
        if GS.ki6:
            return layers.Contains(id)
        return id in layers.Seq()

    @staticmethod
    def zone_get_first_layer(e):
        return e.GetFirstLayer() if GS.ki7 else e.GetLayer()

    @staticmethod
    def footprint_update_local_coords_ki7(fp):
        fp.SetLocalCoord()  # Update the local coordinates

    @staticmethod
    def dummy1(fp):
        """ KiCad 8 doesn't need footprint_update_local_coords """

    @staticmethod
    def expand_text_variables(text, extra_vars=None):
        vars = GS.load_pro_variables()
        new_text = ''
        last = 0
        text_l = len(text)
        for match in GS.vars_regex.finditer(text):
            vname = match.group(1)
            value = vars.get(vname, None)
            if value is None and extra_vars is not None:
                value = extra_vars.get(vname, None)
            if value is None and GS.global_use_os_env_for_expand:
                value = os.environ.get(vname, None)
            if value is None:
                value = '${'+vname+'}'
                logger.warning(W_UNKVAR+"Unknown text variable `{}`".format(vname))
            if match.start():
                new_text += text[last:match.start()]
            new_text += value
            last = match.end()
        if last < text_l:
            new_text += text[last:text_l]
        if new_text != text:
            if GS.debug_level > 3:
                logger.debug('Replacing KiCad text variables: {} -> {}'.format(text, new_text))
        return new_text

    @staticmethod
    def load_pcb_title_block():
        if GS.pcb_title is not None:
            return
        GS.pcb_title = ''
        GS.pcb_date = ''
        GS.pcb_rev = ''
        GS.pcb_comp = ''
        # This is based on InterativeHtmlBom expansion
        title_block = GS.board.GetTitleBlock()
        GS.pcb_date = GS.format_date(GS.expand_text_variables(title_block.GetDate()), GS.pcb_file, 'PCB')
        GS.pcb_title = GS.expand_text_variables(title_block.GetTitle())
        if not GS.pcb_title:
            GS.pcb_title = GS.pcb_basename
        GS.pcb_rev = GS.expand_text_variables(title_block.GetRevision())
        GS.pcb_comp = GS.expand_text_variables(title_block.GetCompany())
        for num in range(9):
            GS.pcb_com[num] = GS.expand_text_variables(GS.get_pcb_comment(title_block, num))
        logger.debug("PCB title: `{}`".format(GS.pcb_title))
        logger.debug("PCB date: `{}`".format(GS.pcb_date))
        logger.debug("PCB revision: `{}`".format(GS.pcb_rev))
        logger.debug("PCB company: `{}`".format(GS.pcb_comp))
        for num in range(4 if GS.ki5 else 9):
            logger.debug("PCB comment {}: `{}`".format(num+1, GS.pcb_com[num]))

    @staticmethod
    def check_pcb():
        if not GS.pcb_file:
            GS.exit_with_error('No PCB file found (*.kicad_pcb), use -b to specify one.', EXIT_BAD_ARGS)

    @staticmethod
    def check_sch():
        if not GS.sch_file:
            GS.exit_with_error('No SCH file found (*.sch), use -e to specify one.', EXIT_BAD_ARGS)

    @staticmethod
    def copy_project(new_pcb_name):
        pro_name = GS.pro_file
        if pro_name is None or not os.path.isfile(pro_name):
            return None
        pro_copy = new_pcb_name.replace('.kicad_pcb', GS.pro_ext)
        logger.debug('Copying project `{}` to `{}`'.format(pro_name, pro_copy))
        copy2(pro_name, pro_copy)
        return pro_copy

    @staticmethod
    def copy_project_sch(sch_dir):
        """ Copy the project file to the temporal dir """
        ext = GS.pro_ext
        source = GS.pro_file
        prj_file = os.path.join(sch_dir, GS.sch_basename+ext)
        if source is not None and os.path.isfile(source):
            logger.debug('Copying project `{}` to `{}`'.format(source, prj_file))
            copy2(source, prj_file)
            GS.fix_page_layout(prj_file)  # Alias for KiConf.fix_page_layout
        else:
            logger.debug('Creating dummy project file `{}`'.format(prj_file))
            # Create a dummy project file to avoid warnings
            f = open(prj_file, 'wt')
            f.close()

    @staticmethod
    def get_pcb_and_pro_names(name):
        if GS.ki5:
            return [name, name.replace('kicad_pcb', 'pro')]
        return [name, name.replace('kicad_pcb', 'kicad_pro'), name.replace('kicad_pcb', 'kicad_prl'),
                name.replace('kicad_pcb', 'kicad_pro-bak'), name.replace('kicad_pcb', 'kicad_prl-bak')]

    @staticmethod
    def remove_pcb_and_pro(name):
        """ Used to remove temporal PCB and project files """
        for fn in GS.get_pcb_and_pro_names(name):
            if os.path.isfile(fn):
                os.remove(fn)

    @staticmethod
    def load_board():
        """ Will be repplaced by kiplot.py """
        raise AssertionError()

    @staticmethod
    def exec_with_retry():
        """ Will be repplaced by kiplot.py """
        raise AssertionError()

    @staticmethod
    def load_board_low_level(file):
        return pcbnew.LoadBoard(file)

    @staticmethod
    def load_sch():
        """ Will be repplaced by kiplot.py """
        raise AssertionError()

    @staticmethod
    def get_useful_layers(useful, layers, include_copper=False):
        """ Filters layers selecting the ones from useful """
        from .layer import Layer
        if include_copper:
            # This is a list of layers that we could add
            useful = {la._id for la in Layer.solve(useful)}
            # Now filter the list of layers using the ones we are interested on
            return [la for la in layers if (include_copper and la.is_copper()) or la._id in useful]
        # Similar but keeping the sorting of useful
        use = {la._id for la in layers}
        return [la for la in Layer.solve(useful) if la._id in use]

    @staticmethod
    def ensure_tool(context, name):
        """ Looks for a mandatory dependency """
        return GS.check_tool_dep(context, name, fatal=True)

    @staticmethod
    def check_tool(context, name):
        """ Looks for a dependency """
        return GS.check_tool_dep(context, name, fatal=False)

    @staticmethod
    def reload_project(pro_name):
        sm = pcbnew.GetSettingsManager()
        sm.UnloadProject(GS.board.GetProject(), False)
        assert sm.LoadProject(pro_name)
        # If we use the old project KiCad SIGSEGV
        GS.board = None

    @staticmethod
    def get_resource_path(name):
        # Try relative to the script
        dir_name = os.path.join(os.path.dirname(__file__), 'resources', name)
        if os.path.isdir(dir_name):
            return dir_name
        # Try using the system level path
        dir_name = os.path.join(os.path.sep, 'usr', 'share', 'kibot', name)
        if os.path.isdir(dir_name):
            return dir_name
        GS.exit_with_error('Missing resource directory `{}`'.format(name), WRONG_INSTALL)

    @staticmethod
    def create_eda_rect(tlx, tly, brx, bry):
        if GS.ki7:
            return pcbnew.BOX2I(pcbnew.VECTOR2I(tlx, tly), pcbnew.VECTOR2I(brx-tlx, bry-tly))
        return pcbnew.EDA_RECT(pcbnew.wxPoint(tlx, tly), pcbnew.wxSize(brx-tlx, bry-tly))

    @staticmethod
    def get_rect_for(bound):
        if GS.ki7:
            pos = bound.GetPosition()
            return pcbnew.wxRect(pcbnew.wxPoint(pos.x, pos.y), pcbnew.wxSize(bound.GetWidth(), bound.GetHeight()))
        return bound.getWxRect()

    @staticmethod
    def get_pad_orientation_in_radians(pad):
        return pad.GetOrientation().AsRadians() if GS.ki7 else pad.GetOrientationRadians()

    @staticmethod
    def iu_to_svg(values, svg_precision):
        """ Converts 1 or more values from KiCad internal IUs to the units used for SVGs.
            For tuples we assume the result is SVG coordinates, for 1 value a scale """
        if GS.ki5:
            if isinstance(values, tuple):
                return tuple(map(lambda x: int(round(x*KICAD5_SVG_SCALE)), values))
            return values*KICAD5_SVG_SCALE
        if GS.ki7:
            if isinstance(values, tuple):
                return tuple(map(GS.to_mm, values))
            return GS.to_mm(values)
        # KiCad 6
        mult = 10.0 ** (svg_precision - 6)
        if isinstance(values, tuple):
            return tuple(map(lambda x: int(round(x*mult)), values))
        return values*mult

    @staticmethod
    def svg_round(val):
        """ KiCad 5/6 uses integers for SVG units, KiCad 7 uses mm and hence floating point """
        if GS.ki7:
            return val
        return int(round(val))

    # @staticmethod
    # def create_wxpoint(x, y):
    #     return pcbnew.wxPoint(x, y)

    @staticmethod
    def is_valid_pcb_shape(g):
        return g.GetShape() != pcbnew.S_SEGMENT or g.GetLength() > 0

    @staticmethod
    def get_start_point(g):
        shape = g.GetShape()
        if GS.ki6:
            if shape == pcbnew.S_CIRCLE:
                # Circle start is circle center
                return g.GetStart()+pcbnew.wxPoint(g.GetRadius(), 0)
            return g.GetStart()
        if shape in [pcbnew.S_ARC, pcbnew.S_CIRCLE]:
            return g.GetArcStart()
        return g.GetStart()

    @staticmethod
    def get_end_point(g):
        shape = g.GetShape()
        if GS.ki6:
            if shape == pcbnew.S_CIRCLE:
                # This is closed start == end
                return g.GetStart()+pcbnew.wxPoint(g.GetRadius(), 0)
            if shape == pcbnew.S_RECT:
                # Also closed start == end
                return g.GetStart()
            return g.GetEnd()
        if shape == pcbnew.S_ARC:
            return g.GetArcEnd()
        if shape == pcbnew.S_CIRCLE:
            return g.GetArcStart()
        return g.GetEnd()

    @staticmethod
    def get_shape_bbox(s):
        """ Bounding box without the width of the trace """
        width = s.GetWidth()
        s.SetWidth(0)
        bbox = s.GetBoundingBox()
        s.SetWidth(width)
        return bbox

    @staticmethod
    def create_module_element(m):
        if GS.ki8:
            return pcbnew.PCB_SHAPE(m)
        if GS.ki6:
            return pcbnew.FP_SHAPE(m)
        return pcbnew.EDGE_MODULE(m)

    @staticmethod
    def create_track(parent):
        if GS.ki6:
            return pcbnew.PCB_TRACK(parent)
        return pcbnew.TRACK(parent)

    @staticmethod
    def create_puntual_track(parent, position, layer):
        track = GS.create_track(parent)
        track.SetStart(position)
        track.SetEnd(position)
        track.SetLayer(layer)
        track.SetWidth(0)
        parent.Add(track)
        return track

    @staticmethod
    def fill_zones(board, zones=None):
        if zones is None:
            zones = board.Zones()
        pcbnew.ZONE_FILLER(board).Fill(zones)
        board.BuildConnectivity()

    @staticmethod
    def get_kiauto_video_name(cmd):
        """ Compute the name for the video captured by KiAuto """
        command = os.path.basename(cmd[0])[:-3]
        subcommand = next(filter(lambda x: x[0] != '-' and (not x[0].isdigit() or x[1] == 'd'), cmd[1:]))
        if command == 'pcbnew':
            return command+'_'+subcommand+'_screencast.ogv'
        if command == 'eeschema':
            return subcommand+'_'+command+'_screencast.ogv'
        return command+'_screencast.ogv'

    @staticmethod
    def add_extra_options(cmd):
        is_gitlab_ci = 'GITLAB_CI' in os.environ
        video_remove = (not GS.debug_enabled) and is_gitlab_ci
        if GS.debug_enabled:
            cmd.insert(1, '-'+'v'*GS.debug_level)
        if GS.debug_enabled or is_gitlab_ci:
            # Forcing record on GitLab CI/CD (black magic)
            cmd.insert(1, '-r')
        if GS.global_kiauto_time_out_scale:
            cmd.insert(1, str(GS.global_kiauto_time_out_scale))
            cmd.insert(1, '--time_out_scale')
        if GS.global_kiauto_wait_start:
            cmd.insert(1, str(GS.global_kiauto_wait_start))
            cmd.insert(1, '--wait_start')
        return cmd, video_remove

    @staticmethod
    def SetExcludeEdgeLayer(po, exclude_edge_layer):
        if not GS.ki7:
            po.SetExcludeEdgeLayer(exclude_edge_layer)

    @staticmethod
    def SetSvgPrecision(po, svg_precision):
        if GS.ki7:
            po.SetSvgPrecision(svg_precision)
        elif GS.ki6:
            po.SetSvgPrecision(svg_precision, False)
        # No ki5 equivalent

    @staticmethod
    def trace_dump():
        if GS.debug_enabled:
            logger.error('Trace stack:')
            (type, value, traceback) = exc_info()
            if traceback is None:
                print(''.join(format_list(extract_stack()[:-2])))
            else:
                print_tb(traceback)

    @staticmethod
    def exit_with_error(msg, level):
        GS.trace_dump()
        if isinstance(msg, tuple):
            for m in msg:
                logger.error(m)
        else:
            logger.error(msg)
        exit(level)
