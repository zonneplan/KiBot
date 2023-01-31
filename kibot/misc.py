# -*- coding: utf-8 -*-
# Copyright (c) 2020-2022 Salvador E. Tropea
# Copyright (c) 2020-2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
""" Miscellaneous definitions """

import re
import os
from contextlib import contextmanager


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
RENDER_3D_ERR = 24
FAILED_EXECUTE = 25
KICOST_ERROR = 26
MISSING_WKS = 27
MISSING_FILES = 28
DIFF_TOO_BIG = 29
NETLIST_DIFF = 30
PS_SCH_PRINT = 31
DXF_SCH_PRINT = 32
HPGL_SCH_PRINT = 33
error_level_to_name = ['NONE',
                       'INTERNAL_ERROR',
                       'WRONG_ARGUMENTS',
                       'USUPPORTED_OPTION',
                       'MISSING_TOOL',
                       'DRC_ERROR',
                       'EXIT_BAD_ARGS',
                       'EXIT_BAD_CONFIG',
                       'NO_PCB_FILE',
                       'NO_SCH_FILE',
                       'ERC_ERROR',
                       'BOM_ERROR',
                       'PDF_SCH_PRINT',
                       'PDF_PCB_PRINT',
                       'PLOT_ERROR',
                       'NO_YAML_MODULE',
                       'NO_PCBNEW_MODULE',
                       'CORRUPTED_PCB',
                       'KICAD2STEP_ERR',
                       'WONT_OVERWRITE',
                       'PCBDRAW_ERR',
                       'SVG_SCH_PRINT',
                       'CORRUPTED_SCH',
                       'WRONG_INSTALL',
                       'RENDER_3D_ERR',
                       'FAILED_EXECUTE',
                       'KICOST_ERROR',
                       'MISSING_WKS',
                       'MISSING_FILES',
                       'DIFF_TOO_BIG',
                       'NETLIST_DIFF',
                       ]
KICOST_SUBMODULE = '../submodules/KiCost/src/kicost'
EXAMPLE_CFG = 'example_template.kibot.yaml'
AUTO_SCALE = 0
KICAD_VERSION_5_99 = 5099000
KICAD_VERSION_6_0_0 = 6000000
KICAD_VERSION_6_0_2 = 6000002
TRY_INSTALL_CHECK = 'Try running the installation checker: kibot-check'

# Internal filter names
IFILT_MECHANICAL = '_mechanical'
IFILT_KICOST_RENAME = '_kicost_rename'
IFILT_KICOST_DNP = '_kicost_dnp'
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
# KiCost distributors
DISTRIBUTORS = ['arrow', 'digikey', 'farnell', 'lcsc', 'mouser', 'newark', 'rs', 'tme']
DISTRIBUTORS_F = [d+'#' for d in DISTRIBUTORS]
DISTRIBUTORS_STUBS = ['part#', '#', 'p#', 'pn', 'vendor#', 'vp#', 'vpn', 'num']
DISTRIBUTORS_STUBS_SEPS = '_- '
# ISO ISO4217 currency codes
# Not all, but the ones we get from the European Central Bank (march 2021)
ISO_CURRENCIES = {'EUR', 'USD', 'JPY', 'BGN', 'CZK', 'DKK', 'GBP', 'HUF', 'PLN', 'RON', 'SEK', 'CHF', 'ISK', 'NOK', 'HRK',
                  'RUB', 'TRY', 'AUD', 'BRL', 'CAD', 'CNY', 'HKD', 'IDR', 'ILS', 'INR', 'KRW', 'MXN', 'MYR', 'NZD', 'PHP',
                  'SGD', 'THB', 'ZAR'}

W_VARCFG = '(W001) '
W_VARPCB = '(W002) '
W_PYCACHE = '(W003) '
W_FIELDCONF = '(W004) '
W_NOHOME = '(W005) '
W_NOUSER = '(W006) '
W_BADSYS = '(W007) '
W_NOCONFIG = '(W008) '
W_NOKIENV = '(W009) '
W_NOLIBS = '(W010) '
W_NODEFSYMLIB = '(W011) '
W_UNKGLOBAL = '(W012) '
W_PCBNOSCH = '(W013) '
W_NONEEDSKIP = '(W014) '
W_UNKOPS = '(W015) '
W_AMBLIST = '(W016) '
W_UNRETOOL = '(W017) '
W_USESVG2 = '(W018) '
W_USEIMAGICK = '(W019) '
W_BADVAL1 = '(W020) '
W_BADVAL2 = '(W021) '
W_BADVAL3 = '(W022) '
W_BADPOLI = '(W023) '
W_POLICOORDS = '(W024) '
W_BADSQUARE = '(W025) '
W_BADCIRCLE = '(W026) '
W_BADARC = '(W027) '
W_BADTEXT = '(W028) '
W_BADPIN = '(W029) '
W_BADCOMP = '(W030) '
W_BADDRAW = '(W031) '
W_UNKDCM = '(W032) '
W_UNKAR = '(W033) '
W_ARNOPATH = '(W034) '
W_ARNOREF = '(W035) '
W_MISCFLD = '(W036) '
W_EXTRASPC = '(W037) '
W_NOLIB = '(W038) '
W_INCPOS = '(W039) '
W_NOANNO = '(W040) '
W_MISSLIB = '(W041) '
W_MISSDCM = '(W042) '
W_MISSCMP = '(W043) '
W_VARSCH = '(W044) '
W_WRONGPASTE = '(W045) '
W_MISFLDNAME = '(W046) '
W_MISS3D = '(W047) '
W_FAILDL = '(W048) '
W_NOLAYER = '(W049) '
W_EMPTYZIP = '(W050) '
W_WRONGCHAR = '(W051) '
W_NOKIVER = '(W052) '
W_EXTNAME = '(W053) '
W_TIMEOUT = '(W054) '
W_MUSTBEINT = '(W055) '
W_NOOUTPUTS = '(W056) '
W_NOTASCII = '(W057) '
W_KIAUTO = '(W058) '
W_NUMSUBPARTS = '(W059) '
W_PARTMULT = '(W060) '
W_EMPTYREN = '(W061) '
W_BADFIELD = '(W062) '
W_UNKDIST = '(W063) '
W_UNKCUR = '(W064) '
W_NONETLIST = '(W065) '
W_NOKICOST = '(W066) '
W_UNKOUT = '(W067) '
W_NOFILTERS = '(W068) '
W_NOVARIANTS = '(W069) '
W_NOENDLIB = '(W070) '
W_NEEDSPCB = '(W071) '
W_NOGLOBALS = '(W072) '
W_EMPTREP = '(W073) '
W_BADCHARS = '(W074) '
W_DATEFORMAT = '(W075) '
W_UNKFLD = '(W076) '
W_ALRDOWN = '(W077) '
W_KICOSTFLD = '(W078) '
W_MIXVARIANT = '(W079) '
W_NOTPDF = '(W080) '
W_NOREF = '(W081) '
W_UNKVAR = '(W082) '
W_WRONGEXT = '(W083) '
W_COLORTHEME = '(W084) '
W_WRONGCOLOR = '(W085) '
W_WKSVERSION = '(W086) '
W_WRONGOAR = '(W087) '
W_ECCLASST = '(W088) '
W_PDMASKFAIL = '(W089) '
W_MISSTOOL = '(W090) '
W_NOTYET = '(W091) '
W_NOMATCH = '(W092) '
W_DOWNTOOL = '(W093) '
W_NOPREFLIGHTS = '(W094) '
W_NOPART = '(W095) '
W_MAXDEPTH = '(W096) '
W_3DRESVER = '(W097) '
W_DOWN3D = '(W098) '
W_MISSREF = '(W099) '
W_COPYOVER = '(W100) '
W_PARITY = '(W101) '
W_MISSFPINFO = '(W102) '
W_PCBDRAW = '(W103) '
W_NOCRTYD = '(W104) '
W_PANELEMPTY = '(W105) '
W_ONWIN = '(W106) '
W_AUTONONE = '(W106) '
W_AUTOPROB = '(W107) '
W_MORERES = '(W108) '
W_NOGROUPS = '(W109) '
W_UNKPCB3DTXT = '(W110) '
W_NOPCB3DBR = '(W111) '
W_NOPCB3DTL = '(W112) '
W_BADPCB3DTXT = '(W113) '
W_UNKPCB3DNAME = '(W114) '
W_BADPCB3DSTK = '(W115) '
W_EEDA3D = '(W116) '
# Somehow arbitrary, the colors are real, but can be different
PCB_MAT_COLORS = {'fr1': "937042", 'fr2': "949d70", 'fr3': "adacb4", 'fr4': "332B16", 'fr5': "6cc290"}
PCB_FINISH_COLORS = {'hal': "8b898c", 'hasl': "8b898c", 'imag': "8b898c", 'enig': "cfb96e", 'enepig': "cfb96e",
                     'none': "d39751", 'hal snpb': "8b898c", 'hal lead-free': "8b898c", 'hard gold': "cfb96e",
                     'immersion silver': "8b898c", 'immersion ag': "8b898c", 'imau': "cfb96e", 'immersion gold': "cfb96e",
                     'immersion au': "cfb96e", 'immersion tin': "8b898c", 'immersion nickel': "cfb96e", 'osp': "d39751",
                     'ht_osp': "d39751"}
SOLDER_COLORS = {'green': ("#285e3a", "#208b47"),
                 'black': ("#1d1918", "#2d2522"),
                 'blue': ("#1b1f44", "#00406a"),
                 'red': ("#812e2a", "#be352b"),
                 'white': ("#bdccc7", "#b7b7ad"),
                 'yellow': ("#73823d", "#f2a756"),
                 'purple': ("#30234a", "#451d70")}
SILK_COLORS = {'black': "0b1013", 'white': "d5dce4"}
# KiCad 6 uses IUs for SVGs, but KiCad 5 uses a very different scale based on inches
KICAD5_SVG_SCALE = 116930/297002200
# Some browser name to pretend
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0'
# Text used to disable 3D models
DISABLE_3D_MODEL_TEXT = '_Disabled_by_KiBot'
RENDERERS = ['pcbdraw', 'render_3d', 'blender_export']
PCB_GENERATORS = ['pcb_variant', 'panelize']
KIKIT_UNIT_ALIASES = {'millimeters': 'mm', 'inches': 'inch', 'mils': 'mil'}


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


def name2make(name):
    return re.sub(r'[ \$\.\\\/]', '_', name)


@contextmanager
def hide_stderr():
    """ Low level stderr suppression, used to hide KiCad bugs. """
    newstderr = os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 2)
    os.close(devnull)
    try:
        yield
    finally:
        os.dup2(newstderr, 2)


def version_str2tuple(ver):
    return tuple(map(int, ver.split('.')))
