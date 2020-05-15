"""
Tests of KiBoM BoM files

The 3Rs.kicad_pcb has R1 on top, R2 on bottom and a thru-hole component R3 on top.
We test:
- Separated N/PTH files with DRL, Gerber and PDF map

For debug information use:
pytest-3 --log-cli-level debug

"""

import os
import sys
# Look for the 'utils' module from where the script is running
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(script_dir))
# Utils import
from utils import context

BOM_DIR = 'BoM'


def test_bom():
    prj = 'bom'
    ctx = context.TestContext('BoM_simple', prj, prj, BOM_DIR)
    ctx.run()
    # Check all outputs are there
    # Default format is PRJ_bom_REVISION
    name = os.path.join(BOM_DIR, prj+'_bom_')
    csv = name+'.csv'
    html = name+'.html'
    ctx.expect_out_file(csv)
    ctx.expect_out_file(html)
    ctx.search_in_file(csv, ['R,R1,100', 'R,R2,200', 'C,C1,1uF'])
    os.remove(os.path.join(ctx.get_board_dir(), 'bom.ini'))
    ctx.clean_up()
