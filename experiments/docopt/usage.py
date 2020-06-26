"""KiPlot

Usage:
  kiplot [-b BOARD_FILE] [-c PLOT_CONFIG] [-d OUT_DIR] [-s SKIP_PRE]
         [-q | -v] [-i]  [TARGET...]
  kiplot -l | --list [-c PLOT_CONFIG]
  kiplot --help-list-outputs
  kiplot --help-output=HELP_OUTPUT
  kiplot --help-outputs
  kiplot --help-preflights
  kiplot -h | --help
  kiplot --version

Arguments:
  TARGET    Outputs to generate, default is all

Options:
  -h, --help                       Show this help message and exit
  -b BOARD, --board-file BOARD     The PCB .kicad-pcb board file
  -c CONFIG, --plot-config CONFIG  The plotting config file to use
  -d OUT_DIR, --out-dir OUT_DIR    The output directory (cwd if not given)
  --help-list-outputs              List supported outputs
  --help-output HELP_OUTPUT        Help for this particular output
  --help-outputs                   List supported outputs and details
  --help-preflights                List supported preflights and details
  -i, --invert-sel                 Generate the outputs not listed as targets
  -l, --list                       List available outputs (in the config file)
  -q, --quiet                      Remove information logs
  -s PRE, --skip-pre PRE           Skip preflights, comma separated or `all`
  -v, --verbose                    Show debugging information
  --version, -V                    Show program's version number and exit

"""
import os
import sys
cur_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(cur_dir)))
print(sys.path)
from kiplot.docopt import docopt

if __name__ == '__main__':
    arguments = docopt(__doc__, version='KiPlot 0.5.0', options_first=True)
    print(arguments)
    print(arguments.__dict__)
