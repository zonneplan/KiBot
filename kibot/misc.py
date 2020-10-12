# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
""" Miscellaneous definitions """

# Error levels
INTERNAL_ERROR = 1    # Unhandled exceptions
WRONG_ARGUMENTS = 2   # This is what argsparse uses
USUPPORTED_OPTION = 3
MISSING_TOOL = 4
DRC_ERROR = 5
EXIT_BAD_ARGS = 6
EXIT_BAD_CONFIG = 7
NO_PCB_FILE = 8
NO_SCH_FILE = 9
ERC_ERROR = 10
BOM_ERROR = 11
PDF_SCH_PRINT = 12
PDF_PCB_PRINT = 13
PLOT_ERROR = 14
NO_YAML_MODULE = 15
NO_PCBNEW_MODULE = 16
CORRUPTED_PCB = 17
KICAD2STEP_ERR = 18
WONT_OVERWRITE = 19
PCBDRAW_ERR = 20
SVG_SCH_PRINT = 21
CORRUPTED_SCH = 22
WRONG_INSTALL = 23

CMD_EESCHEMA_DO = 'eeschema_do'
URL_EESCHEMA_DO = 'https://github.com/INTI-CMNB/kicad-automation-scripts'
CMD_PCBNEW_RUN_DRC = 'pcbnew_do'
URL_PCBNEW_RUN_DRC = URL_EESCHEMA_DO
CMD_PCBNEW_PRINT_LAYERS = 'pcbnew_do'
URL_PCBNEW_PRINT_LAYERS = URL_EESCHEMA_DO
CMD_KIBOM = 'KiBOM_CLI.py'
URL_KIBOM = 'https://github.com/INTI-CMNB/KiBoM'
CMD_IBOM = 'generate_interactive_bom.py'
URL_IBOM = 'https://github.com/INTI-CMNB/InteractiveHtmlBom'
KICAD2STEP = 'kicad2step'
PCBDRAW = 'pcbdraw'
URL_PCBDRAW = 'https://github.com/INTI-CMNB/pcbdraw'
EXAMPLE_CFG = 'example.kibot.yaml'
AUTO_SCALE = 0
KICAD_VERSION_5_99 = 5099000

# Internal filter names
IFILL_MECHANICAL = '_mechanical'
# KiCad 5 GUI values for the attribute
UI_THT = 0       # 1 for KiCad 6
UI_SMD = 1       # 2 for KiCad 6
UI_VIRTUAL = 2   # 12 for KiCad 6
# KiCad 6 module attributes from class_module.h
MOD_THROUGH_HOLE = 1
MOD_SMD = 2
MOD_EXCLUDE_FROM_POS_FILES = 4
MOD_EXCLUDE_FROM_BOM = 8
MOD_BOARD_ONLY = 16  # Footprint has no corresponding symbol
# This is what a virtual component gets when loaded by KiCad 6
MOD_VIRTUAL = MOD_EXCLUDE_FROM_POS_FILES | MOD_EXCLUDE_FROM_BOM

# Supported values for "do not fit"
DNF = {
    "dnf",
    "dnl",
    "dnp",
    "do not fit",
    "do not place",
    "do not load",
    "nofit",
    "nostuff",
    "noplace",
    "noload",
    "not fitted",
    "not loaded",
    "not placed",
    "no stuff",
}
# String matches for marking a component as "do not change" or "fixed"
DNC = {
    "dnc",
    "do not change",
    "no change",
    "fixed",
}

W_VARCFG = '(W1) '
W_VARPCB = '(W2) '
W_PYCACHE = '(W3) '
W_FIELDCONF = '(W4) '
W_NOHOME = '(W5) '
W_NOUSER = '(W6) '
W_BADSYS = '(W7) '
W_NOCONFIG = '(W8) '
W_NOKIENV = '(W9) '
W_NOLIBS = '(W10) '
W_NODEFSYMLIB = '(W11) '
W_UNKGLOBAL = '(W12) '
W_PCBNOSCH = '(W13) '
W_NONEEDSKIP = '(W14) '
W_UNKOPS = '(W15) '
W_AMBLIST = '(W16) '
W_UNRETOOL = '(W17) '
W_USESVG2 = '(W18) '
W_USEIMAGICK = '(W19) '
W_BADVAL1 = '(W20) '
W_BADVAL2 = '(W21) '
W_BADVAL3 = '(W22) '
W_BADPOLI = '(W23) '
W_POLICOORDS = '(W24) '
W_BADSQUARE = '(W25) '
W_BADCIRCLE = '(W26) '
W_BADARC = '(W27) '
W_BADTEXT = '(W28) '
W_BADPIN = '(W29) '
W_BADCOMP = '(W30) '
W_BADDRAW = '(W31) '
W_UNKDCM = '(W32) '
W_UNKAR = '(W33) '
W_ARNOPATH = '(W34) '
W_ARNOREF = '(W35) '
W_MISCFLD = '(W36) '
W_EXTRASPC = '(W37) '
W_NOLIB = '(W38) '
W_INCPOS = '(W39) '
W_NOANNO = '(W40) '
W_MISSLIB = '(W41) '
W_MISSDCM = '(W42) '
W_MISSCMP = '(W43) '
W_VARSCH = '(W44) '


class Rect(object):
    """ What KiCad returns isn't a real wxWidget's wxRect.
        Here I add what I really need """
    def __init__(self):
        self.x1 = None
        self.y1 = None
        self.x2 = None
        self.y2 = None

    def Union(self, wxRect):
        if self.x1 is None:
            self.x1 = wxRect.x
            self.y1 = wxRect.y
            self.x2 = wxRect.x+wxRect.width
            self.y2 = wxRect.y+wxRect.height
        else:
            self.x1 = min(self.x1, wxRect.x)
            self.y1 = min(self.y1, wxRect.y)
            self.x2 = max(self.x2, wxRect.x+wxRect.width)
            self.y2 = max(self.y2, wxRect.y+wxRect.height)
