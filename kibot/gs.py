# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
import re
from datetime import datetime
from sys import exit
from .misc import (EXIT_BAD_ARGS)
from .log import (get_logger)

logger = get_logger(__name__)


class GS(object):
    """
    Class to keep the global settings.
    Is a static class, just a placeholder for some global variables.
    """
    # PCB name and useful parts
    pcb_file = None      # /.../dir/file.sch
    pcb_no_ext = None    # /.../dir/file
    pcb_dir = None       # /.../dir
    pcb_basename = None  # file
    # SCH name and useful parts
    sch_file = None      # /.../dir/pcb.kicad_pcb
    sch_basename = None  # /.../dir/pcb
    sch_no_ext = None    # /.../dir
    sch_dir = None       # pcb
    # Main output dir
    out_dir = None
    filter_file = None
    board = None
    sch = None
    debug_enabled = False
    debug_level = 0
    n = datetime.now()
    today = n.strftime('%Y-%m-%d')
    time = n.strftime('%H-%M-%S')
    kicad_version = ''
    # Data from the SCH because it doesn't have a Python API
    sch_title = None
    sch_date = None
    sch_rev = None
    sch_comp = None
    # Data from the board title block
    pcb_title = None
    pcb_date = None
    pcb_rev = None
    pcb_comp = None
    # Global defaults
    global_output = None
    def_global_output = '%f-%i.%x'

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
        GS.sch_title = ''
        GS.sch_date = ''
        GS.sch_rev = ''
        GS.sch_comp = ''
        re_val = re.compile(r"(\w+)\s+\"([^\"]+)\"")
        with open(GS.sch_file) as f:
            for line in f:
                m = re_val.match(line)
                if not m:
                    if line.startswith("$EndDescr"):
                        break
                    # This line is executed, but coverage fails to detect it
                    continue  # pragma: no cover
                name, val = m.groups()
                if name == "Title":
                    GS.sch_title = val
                elif name == "Date":
                    GS.sch_date = val
                elif name == "Rev":
                    GS.sch_rev = val
                elif name == "Comp":
                    GS.sch_comp = val
        if not GS.sch_date:
            file_mtime = os.path.getmtime(GS.sch_file)
            GS.sch_date = datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d_%H-%M-%S')
        if not GS.sch_title:
            GS.sch_title = GS.sch_basename
        logger.debug("SCH title: `{}`".format(GS.sch_title))
        logger.debug("SCH date: `{}`".format(GS.sch_date))
        logger.debug("SCH revision: `{}`".format(GS.sch_rev))
        logger.debug("SCH company: `{}`".format(GS.sch_comp))

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
        GS.pcb_date = title_block.GetDate()
        if not GS.pcb_date:
            file_mtime = os.path.getmtime(GS.pcb_file)
            GS.pcb_date = datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d_%H-%M-%S')
        GS.pcb_title = title_block.GetTitle()
        if not GS.pcb_title:
            GS.pcb_title = GS.pcb_basename
        GS.pcb_rev = title_block.GetRevision()
        GS.pcb_comp = title_block.GetCompany()
        logger.debug("PCB title: `{}`".format(GS.pcb_title))
        logger.debug("PCB date: `{}`".format(GS.pcb_date))
        logger.debug("PCB revision: `{}`".format(GS.pcb_rev))
        logger.debug("PCB company: `{}`".format(GS.pcb_comp))

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
