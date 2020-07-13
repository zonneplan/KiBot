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
    pcb_file = None
    sch_basename = None
    sch_file = None
    sch_basename = None
    out_dir = None
    filter_file = None
    board = None
    debug_enabled = False
    n = datetime.now()
    today = n.strftime('%Y-%m-%d')
    time = n.strftime('%H-%M-%S')
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

    @staticmethod
    def load_sch_title_block():
        if GS.sch_title is not None:
            return
        GS.sch_title = ''
        GS.sch_date = ''
        GS.sch_rev = ''
        GS.sch_comp = ''
        if not GS.sch_file:
            return
        re_val = re.compile(r"(\w+)\s+\"([^\"]+)\"")
        with open(GS.sch_file) as f:
            for line in f:
                m = re_val.match(line)
                if not m:
                    continue
                name, val = m.groups()
                if name == "Title":
                    GS.sch_title = val
                elif name == "Date":
                    GS.sch_date = val
                elif name == "Rev":
                    GS.sch_rev = val
                elif name == "Comp":
                    GS.sch_comp = val
                elif name == "$EndDescr":
                    break
        if not GS.sch_date:
            file_mtime = os.path.getmtime(GS.sch_file)
            GS.sch_file = datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d_%H-%M-%S')
        GS.sch_basename = os.path.splitext(os.path.basename(GS.sch_file))[0]
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
        if not GS.board:
            return
        # This is based on InterativeHtmlBom expansion
        title_block = GS.board.GetTitleBlock()
        GS.pcb_date = title_block.GetDate()
        if not GS.pcb_date:
            file_mtime = os.path.getmtime(GS.pcb_file)
            GS.pcb_date = datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d_%H-%M-%S')
        GS.pcb_basename = os.path.splitext(os.path.basename(GS.pcb_file))[0]
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
