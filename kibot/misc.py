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
EXAMPLE_CFG = 'example.kibot.yaml'
AUTO_SCALE = 0
