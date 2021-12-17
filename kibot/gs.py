# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from datetime import datetime, date
from sys import exit
from .misc import EXIT_BAD_ARGS, W_DATEFORMAT, KICAD_VERSION_5_99
from .log import get_logger

logger = get_logger(__name__)


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
    # SCH name and useful parts
    sch_file = None      # /.../dir/file.sch
    sch_no_ext = None    # /.../dir/file
    sch_dir = None       # /.../dir
    sch_basename = None  # file
    # Main output dir
    out_dir = None
    out_dir_in_cmd_line = False
    filter_file = None
    board = None
    sch = None
    debug_enabled = False
    debug_level = 0
    n = datetime.now()
    kicad_version = ''
    kicad_conf_path = None
    kicad_share_path = None
    kicad_plugins_dirs = []
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
    sch_com1 = None
    sch_com2 = None
    sch_com3 = None
    sch_com4 = None
    # Data from the board title block
    pcb_title = None
    pcb_date = None
    pcb_rev = None
    pcb_comp = None
    pcb_com1 = None
    pcb_com2 = None
    pcb_com3 = None
    pcb_com4 = None
    # Current variant/s
    variant = None
    # All the outputs
    outputs = None
    # Name for the output we are generating
    current_output = None
    # Global defaults
    #  This is used as default value for classes supporting "output" option
    def_global_output = '%f-%i%v.%x'
    #  This value will overwrite GS.def_global_output if defined
    #  Classes supporting global "output" option must call super().__init__()
    #  after defining its own options to allow Optionable do the overwrite.
    global_from_cli = {}
    global_output = None
    global_dir = None
    global_variant = None
    solved_global_variant = None
    global_kiauto_wait_start = None
    global_kiauto_time_out_scale = None
    global_opts_class = None
    global_3D_model_field = '_3D_model'
    global_date_time_format = None
    global_date_format = None
    global_time_format = None
    global_time_reformat = None
    test_boolean = True

    @staticmethod
    def set_sch(name):
        if name:
            name = os.path.abspath(name)
            GS.sch_file = name
            GS.sch_basename = os.path.splitext(os.path.basename(name))[0]
            GS.sch_no_ext = os.path.splitext(name)[0]
            GS.sch_dir = os.path.dirname(name)

    @staticmethod
    def set_pcb(name):
        if name:
            name = os.path.abspath(name)
            GS.pcb_file = name
            GS.pcb_basename = os.path.splitext(os.path.basename(name))[0]
            GS.pcb_no_ext = os.path.splitext(name)[0]
            GS.pcb_dir = os.path.dirname(name)

    @staticmethod
    def load_sch_title_block():
        if GS.sch_title is not None:
            return
        assert GS.sch is not None
        GS.sch_title = GS.sch.title
        GS.sch_date = GS.sch.date
        GS.sch_rev = GS.sch.revision
        GS.sch_comp = GS.sch.company
        GS.sch_com1 = GS.sch.comment1
        GS.sch_com2 = GS.sch.comment2
        GS.sch_com3 = GS.sch.comment3
        GS.sch_com4 = GS.sch.comment4

    @staticmethod
    def format_date(d, fname, what):
        if not d:
            return datetime.fromtimestamp(os.path.getmtime(fname)).strftime(GS.global_date_time_format)
        elif GS.global_time_reformat:
            try:
                dt = date.fromisoformat(d)
            except ValueError as e:
                logger.warning(W_DATEFORMAT+"Trying to reformat {} time, but not in ISO format ({})".format(what, d))
                logger.warning(W_DATEFORMAT+"Problem: {}".format(e))
                return d
            return dt.strftime(GS.global_date_format)
        return d

    @staticmethod
    def get_pcb_comment(title_block, num):
        if GS.ki6():  # pragma: no cover (Ki6)
            # Backward compatibility ... what's this?
            # Also: Maintaining the same numbers used before (and found in the file) is asking too much?
            return title_block.GetComment(num-1)
        if num == 1:
            return title_block.GetComment1()
        if num == 2:
            return title_block.GetComment2()
        if num == 3:
            return title_block.GetComment3()
        return title_block.GetComment4()

    @staticmethod
    def get_modules():
        if GS.ki6():  # pragma: no cover (Ki6)
            return GS.board.GetFootprints()
        return GS.board.GetModules()

    @staticmethod
    def get_modules_board(board):
        if GS.ki6():  # pragma: no cover (Ki6)
            return board.GetFootprints()
        return board.GetModules()

    @staticmethod
    def get_aux_origin():
        if GS.ki6():  # pragma: no cover (Ki6)
            settings = GS.board.GetDesignSettings()
            return settings.GetAuxOrigin()
        return GS.board.GetAuxOrigin()

    @staticmethod
    def ki6():
        return GS.kicad_version_n >= KICAD_VERSION_5_99

    @staticmethod
    def ki5():
        return GS.kicad_version_n < KICAD_VERSION_5_99

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
        GS.pcb_date = GS.format_date(title_block.GetDate(), GS.pcb_file, 'PCB')
        GS.pcb_title = title_block.GetTitle()
        if not GS.pcb_title:
            GS.pcb_title = GS.pcb_basename
        GS.pcb_rev = title_block.GetRevision()
        GS.pcb_comp = title_block.GetCompany()
        GS.pcb_com1 = GS.get_pcb_comment(title_block, 1)
        GS.pcb_com2 = GS.get_pcb_comment(title_block, 2)
        GS.pcb_com3 = GS.get_pcb_comment(title_block, 3)
        GS.pcb_com4 = GS.get_pcb_comment(title_block, 4)
        logger.debug("PCB title: `{}`".format(GS.pcb_title))
        logger.debug("PCB date: `{}`".format(GS.pcb_date))
        logger.debug("PCB revision: `{}`".format(GS.pcb_rev))
        logger.debug("PCB company: `{}`".format(GS.pcb_comp))
        logger.debug("PCB comment 1: `{}`".format(GS.pcb_com1))
        logger.debug("PCB comment 2: `{}`".format(GS.pcb_com2))
        logger.debug("PCB comment 3: `{}`".format(GS.pcb_com3))
        logger.debug("PCB comment 4: `{}`".format(GS.pcb_com4))

    @staticmethod
    def check_pcb():
        if not GS.pcb_file:
            logger.error('No PCB file found (*.kicad_pcb), use -b to specify one.')
            exit(EXIT_BAD_ARGS)

    @staticmethod
    def check_sch():
        if not GS.sch_file:
            logger.error('No SCH file found (*.sch), use -e to specify one.')
            exit(EXIT_BAD_ARGS)

    @staticmethod
    def load_board():
        """ Will be repplaced by kiplot.py """
        assert False

    @staticmethod
    def load_sch():
        """ Will be repplaced by kiplot.py """
        assert False
